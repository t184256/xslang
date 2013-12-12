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
    if not string: return
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
            if s:
                if s[-1] == '(' or s[-1].isspace():
                    if s[:-1]: yield s[:-1]
                    yield s[-1]; s = ''
            if s:
                if s[-1] == ')': yield s[:-1]; yield ''; yield s[-1]; s = ''
        except StopIteration:
            yield s
            raise StopIteration

def stream_read_single(tstream, token_stream=False):
    s = ''
    while not s or s.isspace():
        s = tstream.next()
        if not s:
            if not token_stream: return None
    if s == '(': s = stream_read_until_closing_brace(tstream)
    if token_stream:
        ts = stream_read_word_or_brace(stream_str(s))
        return ts
    return s

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
        self.parent = parent # A parent brace used for context lookups
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
                n = XInterpreter(self.token_stream,
                                 no_first_brace=True, parent=self)
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
        def XArgInjector(interpreter, arg_, **kwa_):
            arg = arg_
            if not converter is None: arg = converter(arg)
            @XFunction('%s %s=(%s)' % (func, arg_name, arg_))
            def ProxyFunc(*a, **kwa):
                kwa.update(kwa_)
                kwa[arg_name] = arg
                return func(*a, **kwa)
            return ProxyFunc
        return XArgInjector
    return transform

def XFunction_python(s):
    if not ' ' in s.split('(')[0]: s = 'any ' + s # Add 'any' return type
    type_, r = s.split(' ', 1); name, r = s.split('(', 1)
    sign_in, body = r.split(')', 1); params = sign_in.split(' ')
    params = [(p, 'any') if not ':' in p else p.split(':', 1) for p in params]
    s = ''
    assert len(params) > 0
    for pn, pt in params[:-1]:
        s += "XFunction_takes_additional_arg('%s', converter=%s)(\n" % \
                (pn, 'Xc_' + pt)
    pn, pt = params[-1]
    s += "XFunction('%s', converter=%s)(\n" % (name, 'Xc_' + pt)
    s += "lambda interpreter, %s" % params[-1][0]
    s += ''.join(', %s=None' % p[0] for p in params[:-1])
    s += ': Xc_%s( %s )' % (type_, body) +  ')' * len(params)
    return eval(s)

def Xc_str(s):
    if isinstance(s, Xstring): return s.str()
    raise XException('Not an Xstring: ' + str(s))

def Xc_int(i):
    if isinstance(i, Xint): return i.int()
    raise XException('Not an Xint: ' + str(i))

def Xc_tuple(t):
    if isinstance(t, Xtuple): return t.tuple()
    raise XException('Not an Xtuple: ' + str(t))

def Xc_bool(b):
    if isinstance(b, Xtrue): return True
    if isinstance(b, Xfalse): return False
    raise XException('Not an Xbool: ' + str(b))

def Xc_Xstring(s):
    if not isinstance(s, str): raise XException('Not an str: ' + str(s))
    return Xstring(s)

def Xc_Xint(i):
    if not isinstance(i, int): raise XException('Not an int: ' + str(i))
    return Xint(i)

def Xc_Xtuple(i):
    if not isinstance(t, tuple): raise XException('Not a tuple: ' + str(t))
    return Xtuple(i)

def Xc_Xbool(b):
    return Xtrue() if b else Xfalse()
    raise XException('Not an bool: ' + str(b))

Xc_any = lambda x: x

### Standard library ###

class XStringLiteralMutator(XObject):
    def __mutate__(self, interpreter):
        return Xstring(stream_read_single(interpreter.token_stream))
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
        self['join'] = Xstring_join(None, self)
        self['length'] = XStringLengthLazyMutator(self)
        self['set'] = Xset(None, self)
    def __str__(self): return 'X<\'' + self._s + '\'>'
    def str(self): return self._s

@XFunction_takes_additional_arg('varname', converter=Xc_str)
@XFunction('context.set')
def Xset(interpreter, arg, varname=None):
    interpreter.context[varname] = arg
    return Xident
Xget = XFunction_python('context.get(varname:str) interpreter[varname]')

@XFunction_takes_additional_arg('varname', converter=Xc_str)
@XFunction_takes_additional_arg('body', converter=Xc_str)
@XFunction('function.of')
def XfunctionOf(interpreter, arg, varname=None, body=None):
    interpreter.context[varname] = arg
    return XInterpreter(body, parent=interpreter).eval()

Xternary = XFunction_python(
    'operator.ternary(cond:bool if_v else_v) if_v if cond else else_v')

Xif = XFunction_python('operator.if(cond:bool if_body:str else_body:str) ' +
    'XInterpreter(if_body if cond else else_body, parent=interpreter).eval()')

class Xint(XDictionaryObject):
    def __init__(self, i):
        self._i = i
        self['add'] = Xint_add(None, self)
        self['equals'] = Xint_equals(None, self)
        self['string'] = Xint_string(None, self)
        self['subtract'] = Xint_subtract(None, self)
        self['to'] = Xint_to(None, self)
    def __str__(self): return 'X<int:%d>' % self._i
    def int(self): return self._i

Xint_new = XFunction_python('Xint int.new(string:str) int(string)')

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

@XFunction_takes_additional_arg('a', converter=Xc_int)
@XFunction('int.to', converter=Xc_int)
def Xint_to(intepreter, b, a=None):
    return Xtuple(tuple(Xc_Xint(i) for i in range(a, b, 1 if a < b else -1)))

@XFunction_takes_additional_arg('a', converter=Xc_str)
@XFunction('string.concatenate', converter=Xc_str)
def Xstring_concatenate(intepreter, b, a=None): return Xstring(a + b)

Xstring_equals = XFunction_python('Xbool string.equals(a:str b:str) a == b')

@XFunction_takes_additional_arg('s', converter=Xc_str)
@XFunction('string.join', converter=Xc_tuple)
def Xstring_join(intepreter, t, s=None):
    return Xc_Xstring(s.join(Xc_str(x) for x in t))
Xstring_join = XFunction_python(
    'Xstring string.join(s:str t:tuple) s.join(Xc_str(x) for x in t)')

@XFunction('string.length', converter=Xc_str)
def Xstring_length(intepreter, s): return Xc_Xint(len(s))

class XStringLengthLazyMutator(XObject):
    def __init__(self, Xstr): self._Xstr = Xstr
    def __mutate__(self, interpreter):
        return Xint(self._xstr)

class Xtuple(XDictionaryObject):
    def __init__(self, t):
        self._t = t
        self['add'] = Xtuple_add(None, self)
        self['get'] = Xtuple_get(None, self)
        self['equals'] = Xtuple_equals(None, self)
        self['filter'] = Xtuple_filter(None, self)
        self['length'] = Xtuple_length(None, self)
        self['map'] = Xtuple_map(None, self)
        self['reduce'] = Xtuple_reduce(None, self)
    def __str__(self): return 'X<%s>' % ','.join(str(x) for x in self._t)
    def tuple(self): return self._t

@XFunction_takes_additional_arg('t', converter=Xc_tuple)
@XFunction('tuple.add')
def Xtuple_add(intepreter, e, t=None): return Xtuple(t + tuple([e]))

@XFunction_takes_additional_arg('t', converter=Xc_tuple)
@XFunction('tuple.get', converter=Xc_int)
def Xtuple_get(intepreter, i, t=None):
    if not (i >= 0 and i < len(t)):
        raise XException('Out of bounds: %d/%d' % (i, len(t)))
    return t[i]

@XFunction_takes_additional_arg('t1', converter=Xc_tuple)
@XFunction('tuple.equals', converter=Xc_tuple)
def Xtuple_equals(intepreter, t2, t1=None):
    def compare(e1, e2):
        if e1 == e2: return True
        if type(e1) != type(e2): return False
        if not (isinstance(e1, XDictionaryObject) and
                isinstance(e2, XDictionaryObject)): return False
        if not 'equals' in e1: return False
        return Xc_bool(e1['equals'](None, e2))
    if len(t1) != len(t2): return Xc_Xbool(False)
    return Xc_Xbool(all(compare(e1, e2) for e1, e2 in zip(t1, t2)))

@XFunction('tuple.length', converter=Xc_tuple)
def Xtuple_length(intepreter, t): return Xc_Xint(len(t))

@XFunction_takes_additional_arg('t', converter=Xc_tuple)
@XFunction('tuple.map')
def Xtuple_map(i, func, t=None):
    interpreter = i
    return Xtuple(tuple(func(interpreter, x) for x in t))

@XFunction_takes_additional_arg('t', converter=Xc_tuple)
@XFunction('tuple.filter')
def Xtuple_filter(i, func, t=None):
    interpreter = i
    return Xtuple(tuple(x for x in t if Xc_bool(func(interpreter, x))))

@XFunction_takes_additional_arg('t', converter=Xc_tuple)
@XFunction('tuple.reduce')
def Xtuple_reduce(i, func, t=None):
    return reduce(lambda acc, x: func(i, acc)(i, x), t)


### Syntax transformations ###

def stream_detokenize_stream(tstream):
    while True:
        s = tstream.next()
        if not s: continue
        while s:
            c, s = s[0], s[1:]
            yield c

def stream_tokens_of_a_brace(tstream, opened=False):
    char_stream = stream_detokenize_stream(tstream)
    if not opened: assert(char_stream.next() == '(')
    s = stream_read_until_closing_brace(char_stream, 1 if not opened else 0)
    return stream_read_word_or_brace(stream_str(s))

def tokens_forming_a_literal(l):
    return (' ', '(', '#', ' ', '(', l, '', ')', '', ')')

def tokens_walking_a_path(*p):
    r = ('(', 'xslang', ' ')
    for t in p: r += tokens_forming_a_literal(t)
    return r + (' ',)

def dotty_literals(stream):
    while True:
        t = stream.next()
        if not '.' in t: yield t; continue
        if t == '.':
            inside = ''.join(stream_tokens_of_a_brace(stream))
            for z in tokens_forming_a_literal(inside): yield z
            continue
        if '.' in t and not t.startswith('.'):
            yield '('
            p, t = t.split('.', 1)
            t = '.' + t
            yield p; yield ' '
            while t.startswith('.') and '.' in t[1:]:
                p, t = t[1:].split('.', 1)
                t = '.' + t
                for z in tokens_forming_a_literal(p): yield z
            if t:
                for z in tokens_forming_a_literal(t[1:]): yield z
            yield ''; yield ')'
            continue
        for z in tokens_forming_a_literal(t[1:]): yield z

def surround(what, with_=' '):
    # TODO: reimplement with a simplistic replace, left and right paddings
    def surr(tstream):
        for t in tstream:
            if not what in t: yield t
            else:
                l = []
                while what in t:
                    a, t = t.split(what, 1)
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

def replace_(c, pairs):
    for what, with_ in pairs:
        c = c.replace(what, with_)
    return c

def creplace(*pairs):
    def sur(cstream):
        for c in cstream:
            for z in replace_(c, pairs): yield z
    return composition(stream_detokenize_stream, sur, stream_read_word_or_brace)

def curly_braced_functions_(tstream):
    while True:
        t = tstream.next()
        if t != '{': yield t
        else:
            for z in curly_braced_functions_inside_a_brace(tstream): yield z
def curly_braced_functions_inside_a_brace(tstream):
    s = ''
    while not s or s[-1] not in '|}': s += tstream.next()
    s, c = s[:-1], s[-1]
    argnames = s.split()
    if c == '|': # We have a {x y | z}-like block, yield function.of...
        for argname in argnames:
            for z in (tokens_walking_a_path('function', 'of', argname) +
                    (' ', '(', '#', ' ', '(')): yield z
        s = ''
        while True:
            s += tstream.next()
            if s.count('}') - s.count('{') == 1: break
        s = s[:-1]
    elif c == '}': # We have a {x y z}-like block, yield a literal
        for z in '(', '#', ' ', '(': yield z
        s = s

    int_tstream = stream_read_word_or_brace(stream_str(s))
    for t in int_tstream:
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
    return (tokens_walking_a_path('type', 'int', 'new', int_str) + (')',))

def int_auto(stream):
    while True:
        t = stream.next()
        if t:
            if t.isdigit() or (t[0] == '-' and t[1:].isdigit()):
                for z in tokens_forming_an_int(t): yield z
                continue
        yield t

def tuple_auto_empties(stream):
    no_read = False
    while True:
        if not no_read: t = stream.next()
        no_read = False
        if t == '[]':
            for z in tokens_walking_a_path('type', 'tuple', 'empty'):
                yield z
            yield ''; yield ')'
        elif t == '[':
            l = [t, stream.next()]
            while not l[-1] or l[-1].isspace(): l.append(stream.next())
            if l[-1] == ']':
                # Empty tuple
                for z in tokens_walking_a_path('type', 'tuple', 'empty'):
                    yield z
                yield ''; yield ')'
            else:
                if l[-1] in ('[', '[]'):
                    t = l[-1]
                    del l[-1]
                    no_read = True
                for z in l: yield z
        else: yield t

tuple_auto_creplace = creplace(
    ('[', ' (xslang (# type) (# tuple) (# empty) (# add) ('),
    (',', ') (# add) ('),
    (']', ')) '),
)
tuple_auto = composition(
    surround('['), surround(']'),
    tuple_auto_empties, tuple_auto_creplace
)

rich = composition(tuple_auto, curly_braced_functions, int_auto, dotty_literals)

TRANSFORMATIONS = {
    'dotty_literals': dotty_literals,
    'curly_braced_functions': curly_braced_functions,
    'int_auto': int_auto,
    'tuple_auto': tuple_auto,
    'rich': rich,
}

def expand(string, transformation_name='rich'):
    tr = TRANSFORMATIONS[transformation_name]
    return '$%s$' % ''.join(tr(stream_read_word_or_brace(stream_str(string))))

@XFunction('syntax.enable')
def XsyntaxEnable(interpreter, transformation_name):
    transformation_name = Xc_str(transformation_name)
    transform = TRANSFORMATIONS[transformation_name]
    interpreter.token_stream = transform(interpreter.token_stream)
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
            'to': Xint_to,
        }),
        'none': Xnone,
        'string': XDictionaryObject({
            'concatenate': Xstring_concatenate,
            'constants': XDictionaryObject({
                'newline': Xstring('\n'),
            }),
            'equals': Xstring_equals,
            'join': Xstring_join,
            'length': Xstring_length,
            'literal': XStringLiteralMutator(),
        }),
        'tuple': XDictionaryObject({
            'add': Xtuple_add,
            'empty': Xtuple(tuple()),
            'equals': Xtuple_equals,
            'get': Xtuple_get,
            'filter': Xtuple_filter,
            'length': Xtuple_length,
            'map': Xtuple_map,
            'reduce': Xtuple_reduce,
        }),
    }),
})

if __name__ == '__main__': print XInterpreter(raw_input()).eval()
