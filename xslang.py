#!/usr/bin/python

# an eXtensible Syntax LANGuage experiment
# Copyright (C) 2013 Sosedkin Alexander <monk@unboiled.info>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

### Definition of the basics ###

class XObject(object):
    def __str__(self): return 'X<' + object.__str__(self) + '>'

class XException(Exception): pass

class XBool(XObject): pass
class Xtrue(XBool): pass
class Xfalse(XBool): pass
class Xnone(XObject): pass

### Streaming ###

def stream_str(string):
    while True:
        c, string = string[0], string[1:]
        yield c
        if not string: return

def stream_read_until_closing_brace(tstream, opened=1):
    s, b = '', opened
    while b > 0 or not ('(' in s or ')' in s):
        c = tstream.next(); s += c
        if c == '(': b += 1
        elif c == ')': b -= 1
        if c.isspace() or c in '()':
            if b == 0:
                return s[:-1]
    return s[:-1]

def stream_read_word_or_brace(stream):
    """Converts '((xslang operator) ident)') to
       ['(', '(', 'xslang', ' ', 'operator', '', ')', ' ', 'ident', '', ')']"""
    s = ''
    while True:
        try:
            s += stream.next()
            #print 's "%s"' % s
            if s:
                if s[-1] == '(' or s[-1].isspace():
                    if s[:-1]: yield s[:-1]
                    yield s[-1]; s = ''
            if s:
                if s[-1] == ')': yield s[:-1]; yield ''; yield s[-1]; s = ''
        except StopIteration:
            yield s
            raise StopIteration

### The interpreter ###

class XInterpreter(object):
    def __init__(self, stream, root_obj=None, root_obj_name='xslang', \
                no_first_brace=False, parent=None):
        self.context = {root_obj_name: root_obj or xslang_rootobj}
        self.context['#'] = XStringLiteralMutator()
        self.token_stream = stream_read_word_or_brace(
                stream_str('(' + stream + ')')
                if isinstance(stream, str) else stream
        )
        self.parent = parent
        self.no_first_brace = no_first_brace
        self.previous = [] # For dirty introspection
        self.currently_mutating = None # For dirty introspection

    def __getitem__(self, n, maxdepth=-1):
        if n in self.context: return self.context[n]
        if not self.parent: raise XException(n + ' not found!')
        if maxdepth == 0: raise XException(n + ' not found here!')
        return self.parent.__getitem__(n, maxdepth - 1)

    def __contains__(self, n):
        if n in self.context: return True
        if not self.parent: return False
        return n in self.parent

    def eval(self):
        if not self.no_first_brace:
           if self.token_stream.next() != '(': raise XException('No (')
        f = None
        while True:
            n = self.token_stream.next()
            if n.isspace() or n == '': continue
            elif n == '(':
                n = XInterpreter(self.token_stream, no_first_brace=True, parent=self)
                self.currently_mutating = n
                n = n.eval()
            elif n == ')': return f
            if (isinstance(n, str)):
                if n in self: n = self[n]
                else: raise XException('No ' + n + ' in current context!')
            if f is None: f = n
            else: f = f(self, n)
            #print f
            assert isinstance(f, XObject)
            while '__mutate__' in dir(f):
                self.currently_mutating = f
                transformed = f.__mutate__(interpreter=self)
                #print f, 'TRANSFORMED INTO', transformed
                if transformed is None: break # Cancel transformation
                else: f = transformed
                assert isinstance(f, XObject)
            self.previous.append(f)
            self.currently_mutating = None

### Helper decorators for standard library ###

def XFunction(name=None, converter=None):
    def transform(func):
        class XFunc(XObject):
            def __call__(self, interpreter, arg, *a, **kwa):
                if not converter is None: arg = converter(arg)
                return func(interpreter, arg, *a, **kwa)
            def __str__(self): return 'X<' + name + '>' \
                    if name is not None else XObject.__str__(self)
        return XFunc()
    return transform

def XFunction_takes_additional_arg(arg_name, converter=None):
    def transform(func):
        @XFunction('%s %s=(???)' % (str(func), arg_name))
        def XArgInjector(interpreter, arg, **kwa_):
            if not converter is None: arg = converter(arg)
            @XFunction('%s %s=(%s)' % (func, arg_name, arg))
            def ProxyFunc(*a, **kwa):
                kwa.update(kwa_)
                kwa[arg_name] = arg
                return func(*a, **kwa)
            return ProxyFunc
        return XArgInjector
    return transform

def Xc_str(s):
    if isinstance(s, Xstring): return s.str()
    raise XException('Not an Xstring: ' + str(s))

def Xc_int(i):
    if isinstance(i, Xint): return i.int()
    raise XException('Not an Xint: ' + str(i))

def Xc_bool(b):
    if isinstance(b, Xtrue): return True
    if isinstance(b, Xfalse): return False
    raise XException('Not an Xbool: ' + str(b))

def Xc_Xbool(b):
    return Xtrue() if b else Xfalse()
    raise XException('Not an bool: ' + str(b))

### Standard library ###

class XStringLiteralMutator(XObject):
    def __mutate__(self, interpreter):
        s = ''
        while not s or s.isspace():
            s = interpreter.token_stream.next()
            if not s: return None
        if s == '(': s = stream_read_until_closing_brace(interpreter.token_stream)
        return Xstring(s)
    def __str__(self): return 'X<"???">'

@XFunction('ident')
def Xident(interpreter, arg): return arg
@XFunction('ignore')
def Xignore(interpreter, arg): return Xident

class XDictionaryObject(XObject, dict):
    def __call__(self, interpreter, arg):
        arg = Xc_str(arg)
        if not arg in self: raise XException('"%s" not found!' % arg)
        return self[arg]
    def __str__(self): return 'XDICT<' + ','.join(sorted(self.keys())) + '>'

class Xstring(XDictionaryObject):
    def __init__(self, s):
        self._s = s
        self['concatenate'] = Xstring_concatenate(None, self)
        self['equals'] = Xstring_equals(None, self)
        self['set'] = Xset(None, self)
    def __str__(self): return 'X<\'' + self._s + '\'>'
    def str(self): return self._s

@XFunction_takes_additional_arg('varname', converter=Xc_str)
@XFunction('set')
def Xset(interpreter, arg, varname=None):
    interpreter.context[varname] = arg
    return Xident

@XFunction('get', converter=Xc_str)
def Xget(interpreter, varname):
    return interpreter.context[varname]

@XFunction_takes_additional_arg('varname', converter=Xc_str)
@XFunction_takes_additional_arg('body', converter=Xc_str)
@XFunction('function.of')
def XfunctionOf(interpreter, arg, varname=None, body=None):
    interpreter.context[varname] = arg
    return XInterpreter(body, parent=interpreter).eval()

@XFunction_takes_additional_arg('condition', converter=Xc_bool)
@XFunction_takes_additional_arg('if_val')
@XFunction('ternary')
def Xternary(interpreter, else_val, if_val, condition=None):
    return if_val if condition else else_val

@XFunction_takes_additional_arg('condition', converter=Xc_bool)
@XFunction_takes_additional_arg('if_body', converter=Xc_str)
@XFunction('if', converter=Xc_str)
def Xif(interpreter, else_body, if_body, condition=None):
    body = if_body if condition else else_body
    p = interpreter
    return XInterpreter(body, parent=p).eval()

class Xint(XDictionaryObject):
    def __init__(self, i):
        self._i = i
        self['add'] = Xint_add(None, self)
        self['equals'] = Xint_equals(None, self)
        self['string'] = Xint_string(None, self)
        self['subtract'] = Xint_subtract(None, self)
    def __str__(self): return 'X<int:%d>' % self._i
    def int(self): return self._i

@XFunction('int.new', converter=Xc_str)
def Xint_new(intepreter, string):
    return Xint(int(string))

@XFunction_takes_additional_arg('a', converter=Xc_int)
@XFunction('int.add', converter=Xc_int)
def Xint_add(intepreter, b, a=None):
    return Xint(a + b)

@XFunction_takes_additional_arg('a', converter=Xc_int)
@XFunction('int.equals', converter=Xc_int)
def Xint_equals(intepreter, b, a=None): return Xc_Xbool(a == b)

@XFunction('int.string', converter=Xc_int)
def Xint_string(intepreter, i):
    return Xstring(str(i))

@XFunction_takes_additional_arg('a', converter=Xc_int)
@XFunction('int.subtract', converter=Xc_int)
def Xint_subtract(intepreter, b, a=None): return Xint(a - b)

@XFunction_takes_additional_arg('a', converter=Xc_str)
@XFunction('string.concatenate', converter=Xc_str)
def Xstring_concatenate(intepreter, b, a=None): return Xstring(a + b)

@XFunction_takes_additional_arg('a', converter=Xc_str)
@XFunction('string.equals', converter=Xc_str)
def Xstring_equals(intepreter, b, a=None): return Xc_Xbool(a == b)

### Syntax transformations ###

def stream_detokenize_stream(tstream):
    while True:
        s = tstream.next()
        if not s: continue
        while s:
            c, s = s[0], s[1:]
            yield c

def stream_tokens_of_a_brace(tstream):
    char_stream = stream_detokenize_stream(tstream)
    assert(char_stream.next() == '(')
    s = stream_read_until_closing_brace(char_stream, 1)
    return stream_read_word_or_brace(stream_str(s))

def tokens_forming_a_literal(l):
    return (' ', '(', '#', ' ', '(', l, '', ')', '', ')')

def dotty_literals(stream):
    while True:
        t = stream.next()
        #print 't', t
        if not '.' in t: yield t; continue
        if t == '.':
            inside = ''.join(stream_tokens_of_a_brace(stream))
            for z in tokens_forming_a_literal(inside): yield z
            continue
        if '.' in t and not t.startswith('.'):
            p, t = t.split('.', 1)
            t = '.' + t
            yield p; yield ' '
        while t.startswith('.') and '.' in t[1:]:
            p, t = t[1:].split('.', 1)
            t = '.' + t
            for z in tokens_forming_a_literal(p): yield z
        for z in tokens_forming_a_literal(t[1:]): yield z

def surround(what, with_=' '):
    # TODO: reimplement with a simplistic replace, left and right paddings
    def surr(tstream):
        for t in tstream:
            if not what in t: yield t
            else:
                l = []
                while '{' in t:
                    a, t = t.split('{', 1)
                    l += [a, with_, what, with_]
                for z in l: yield z
                if t: yield t
    return surr

def composition(ti, *ts):
    def composed(stream):
        f = ti(stream)
        for t in ts: f = t(f)
        return f
    return composed

def curly_braced_functions_(tstream):
    while True:
        t = tstream.next()
        #print 't "%s"' % t
        if t != '{': yield t
        else:
            #print '{!!!'
            #ts = list(curly_braced_functions_inside_a_brace(tstream))
            #print 'ts', ''.join(ts)
            #for z in ts: yield z
            for z in curly_braced_functions_inside_a_brace(tstream): yield z
        #print 'DONE'
def curly_braced_functions_inside_a_brace(tstream):
    #print 'INSIDE'
    s = ''
    while not s or s[-1] not in '|}': s += tstream.next()
    #print 's', s
    s, c = s[:-1], s[-1]
    argnames = s.split()
    #print 'argnames', argnames
    if c == '|': # We have a {x y | z}-like block, yield function.of...
        for argname in argnames:
            for z in (('(', 'xslang',) +
                      tokens_forming_a_literal('function') +
                      tokens_forming_a_literal('of') +
                      tokens_forming_a_literal(argname) +
                      (' ', '(', '#', ' ', '(')): yield z
        s = ''
        while True:
            s += tstream.next()
            if s.count('}') - s.count('{') == 1: break
        s = s[:-1]
    elif c == '}': # We have a {x y z}-like block, yield a literal
        for z in '(', '#', ' ', '(': yield z
        s = s

    #print 'cont "%s"' % s
    int_tstream = stream_read_word_or_brace(stream_str(s))
    for t in int_tstream:
        #print 'it', t
        if t == '}': break
        elif t == '{':
            for z in curly_braced_functions_inside_a_brace(int_tstream):
                yield z
        else: yield t

    if c == '|':
        for z in ('', ')') * (len(argnames) * 3): yield z
    elif c == '}':
        for z in ('', ')') * 2: yield z

curly_braced_functions = composition(
    surround('{'), surround('}'), surround('|'), curly_braced_functions_
)

def tokens_forming_an_int(int_str):
    return (('(', 'xslang ') + tokens_forming_a_literal('type') +
            tokens_forming_a_literal('int') + tokens_forming_a_literal('new') +
            tokens_forming_a_literal(int_str) + (')',))

def int_auto(stream):
    while True:
        t = stream.next()
        if t:
            if t.isdigit() or (t[0] == '-' and t[1:].isdigit()):
                for z in tokens_forming_an_int(t): yield z
                continue
        yield t

rich = composition(int_auto, curly_braced_functions, dotty_literals)
def rich_expand(string):
    return '$%s$' % ''.join(rich(stream_read_word_or_brace(stream_str(string))))

TRANSFORMATIONS = {
    'dotty_literals': dotty_literals,
    'curly_braced_functions': curly_braced_functions,
    'int_auto': int_auto,
    'rich': rich,
}

@XFunction('syntax.enable')
def XsyntaxEnable(interpreter, transformation_name):
    transformation_name = Xc_str(transformation_name)
    transform = TRANSFORMATIONS[transformation_name]
#    print 'transformation', transform
    interpreter.token_stream = transform(interpreter.token_stream)
#    print 'transformed', interpreter.token_stream
#    raise Exception(list(interpreter.token_stream))
#    raise Exception(''.join(interpreter.token_stream))
#    stream = transform(interpreter.stream)
#    return XInterpreter(stream, parent=interpreter).eval()
#    interpreter.wrap_stream(transform)
    return Xident

xslang_rootobj = XDictionaryObject({
    'context': XDictionaryObject({
        'set': Xset,
        'get': Xget,
    }),
    'function': XDictionaryObject({
        'of': XfunctionOf,
    }),
    'operator': XDictionaryObject({
        'ident': Xident,
        'ignore': Xignore,
        'ternary': Xternary,
        'if': Xif,
    }),
    'package': XDictionaryObject({}),
    'syntax': XDictionaryObject({
            'enable': XsyntaxEnable,
    }),
    'type': XDictionaryObject({
        'bool': XDictionaryObject({
            'true': Xtrue(),
            'false': Xfalse(),
        }),
        'int': XDictionaryObject({
            'add': Xint_add,
            'equals': Xint_equals,
            'new': Xint_new,
            'string': Xint_string,
            'subtract': Xint_subtract,
        }),
        'none': Xnone,
        'string': XDictionaryObject({
            'concatenate': Xstring_concatenate,
            'equals': Xstring_equals,
            'literal': XStringLiteralMutator(),
        }),
    }),
})

if __name__ == '__main__': print XInterpreter(raw_input()).eval()
