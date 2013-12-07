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

def Xc_bool(s):
    if isinstance(s, Xtrue): return True
    if isinstance(s, Xfalse): return False
    raise XException('Not an Xbool: ' + str(s))

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
    def __init__(self, s): self._s = s
    def __str__(self): return 'X<\'' + self._s + '\'>'
    def str(self): return self._s

@XFunction('set')
@XFunction_takes_additional_arg('varname', converter=Xc_str)
def Xset(interpreter, arg, varname=None):
    interpreter.context[varname] = arg
    return Xident

@XFunction('get')
def Xget(interpreter, varname):
    varname = Xc_str(varname)
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

def tokens_forming_a_literal(l): return (' ', '(', '#', ' ', l, '', ')')

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
    if c == '}': # We have a {x y z}-like block, yield a literal
        for z in tokens_forming_a_literal(s):
            yield z
    elif c == '|': # We have a {x y | z}-like block, yield function.of...
        argnames = s.split()
        #print 'argnames', argnames
        for argname in argnames:
            for z in (('(', 'xslang',) +
                      tokens_forming_a_literal('function') +
                      tokens_forming_a_literal('of') +
                      tokens_forming_a_literal(argname) +
                      (' ', '(', '#', ' ', '(')): yield z
        contents = ''
        while True:
            contents += tstream.next()
            if contents.count('}') - contents.count('{') == 1: break
        contents = contents[:-1]
        #print 'cont', contents
        int_tstream = stream_read_word_or_brace(stream_str(contents))
        for t in int_tstream:
            #print 'it', t
            if t == '}': break
            elif t == '{':
                for z in curly_braced_functions_inside_a_brace(int_tstream):
                    yield z
            else: yield t
        #print ')))'
        for argname in argnames:
            for z in '', ')', '', ')', '', ')': yield z
curly_braced_functions = composition(
    surround('{'), surround('}'), surround('|'), curly_braced_functions_
)

TRANSFORMATIONS = {
    'dotty_literals': dotty_literals,
    'curly_braced_functions': curly_braced_functions,
    'rich': composition(curly_braced_functions, dotty_literals),
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
    }),
    'package': XDictionaryObject({}),
    'syntax': XDictionaryObject({
            'enable': XsyntaxEnable,
    }),
    'type': XDictionaryObject({
        'none': Xnone,
        'bool': XDictionaryObject({
            'true': Xtrue(),
            'false': Xfalse(),
        }),
    }),
})

if __name__ == '__main__': print XInterpreter(raw_input()).eval()
