#!/usr/bin/python

# an eXtensible Syntax LANGuage experiment - Joys Of Partial Application
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

import types

class JOPAObject(object):
    def __init__(self, takes_literal=False):
        self.takes_literal = takes_literal

class JOPAObjectNone(JOPAObject): pass
class JOPABoolean(JOPAObject): pass
class JOPATrue(JOPABoolean):
    def __str__(self): return 'true'
class JOPAFalse(JOPABoolean):
    def __str__(self): return 'false'
def JOPABool(obj): return JOPATrue() if obj else JOPAFalse()

class JOPAObjectPackage(JOPAObject):
    def __init__(self, name, dic=None):
        JOPAObject.__init__(self)
        self.dic, self.name = dic or {}, name
    def __call__(self, arg, brace):
        if arg in self.dic: return self.dic[arg]
        raise JOPAException('"%s" not found in "%s"' % (str(arg), str(self)))
    def __str__(self): return self.name

class JOPAString(JOPAObject):
    def __init__(self, initial_string=None, takes_literal=False):
        JOPAObject.__init__(self, takes_literal=takes_literal)
        self._str = initial_string or ''
    def __call__(self, arg, brace):
        return JOPAString(initial_string=(self._str + str(arg)))
    def __str__(self):
        return self._str

class JOPASyntaxEnable(JOPAObject):
    def __init__(self):
        JOPAObject.__init__(self, takes_literal=True)
    def __call__(self, arg, brace):
        brace.source.wrap_subsource(TRANSFORMATIONS[str(arg)])
        return JOPAIdent
    def __str__(self): return 'jopa.syntax.enable'

jopa_ro = JOPAObjectPackage('jopa root package', {
    'operator': JOPAObjectPackage('jopa.operator package'),
    'function': JOPAObjectPackage('jopa.function package'),
    'context': JOPAObjectPackage('jopa.context package'),
    'bool': JOPAObjectPackage('jopa.bool package', {
        'true': JOPATrue(),
        'false': JOPAFalse(),
    }),
    'string': JOPAObjectPackage('jopa.string package', {
        'create': JOPAString(),
        'literal': JOPAString(takes_literal=True),
        'lbrace': JOPAString('('),
        'rbrace': JOPAString(')'),
        'space': JOPAString(' '),
        'tab': JOPAString('\t'),
        'newline': JOPAString('\n'),
    }),
    'syntax': JOPAObjectPackage('jopa.syntax package', {
        'enable': JOPASyntaxEnable(),
    }),
})

### The interpreter: the Brace ###

class JOPAException(Exception): pass

SQMAP = {'[':'(', ']':')'}
def translate(source, func):
    c = source(); return func(c) if not c is None else None
def translate_remap(src, MAP):
    return translate(src, lambda c: MAP[c] if c in MAP else c)

def consume_until(source, char, exception=None):
    s = ''
    while True:
        c = source()
        if c is None:
            if exception is not None: raise exception
            break
        if c == char: break
        s += c
    return s
def curly_braced_functions(source):
    while True:
        c = None
        while True:
            c = source()
            if c == '{': break
            yield c
        first = consume_until(source, '|', JOPAException('No | inside {|}'))
        first = '(jopa function of %s (' % first
        while first:
            yield first[0]
            first = first[1:]
        while True:
            c = source()
            if c is None: raise JOPAException('No }')
            if c == '}': break
            yield c
        yield ')'; yield ')'

def generator_to_callable(generator, *a, **kwa):
    gen = generator(*a, **kwa)
    def call():
        try:
            return gen.next()
        except StopIteration, e:
            return None
    return call

TRANSFORMATIONS = {
    'square_brackets': lambda src: lambda: translate_remap(src, SQMAP),
    'curly_braced_functions': lambda src:
    generator_to_callable(curly_braced_functions, src)
}

class UnpeekableStringSource(object):
    def __init__(self, string):
        self.string = string
    def __call__(self):
        if not self.string: return None
        c = self.string[0]
        self.string = self.string[1:]
        return c

class Source(object):
    def __init__(self, subsource=None):
        self.subsource = subsource
        if isinstance(subsource, str):
            self.subsource = UnpeekableStringSource(subsource)
        if subsource is None:
            self.s = ''
        else:
            self.s = self.subsource()
    def peek(self): return self.s[0] if self.s else None
    def __call__(self):
        if len(self.s) > 1:
            c = self.s[0]
            self.s = self.s[1:]
            return c
        elif len(self.s) == 1:
            c = self.s
            if self.subsource is None: self.s = ''; return c
            n = self.subsource()
            if not n is None:
                self.s = n
            else:
                self.func = None
                self.s = ''
            return c
        else:
            return None
    def wrap_subsource(self, wrapper):
        self.subsource = wrapper(self.subsource)

class JOPABrace(JOPAObject):
    def __init__(self, source, parent=None, rootobj=None):
        if isinstance(source, str): source = Source(source)
        self.source, self.parent = source, parent
        self.context = {}
        if not rootobj is None: self.context['jopa'] = rootobj
        self.string = None
        self.exposed_current_state = None

    def __getitem__(self, n, maxdepth=-1):
        if n in self.context: return self.context[n]
        if not self.parent: raise JOPAException(n + ' not found!')
        if maxdepth == 0: raise JOPAException(n + ' not found here!')
        return self.parent.__getitem__(n, maxdepth - 1)

    def __contains__(self, n):
        if n in self.context: return True
        if not self.parent: return False
        return n in self.parent

    def _suckup(self):
        if not self.source() == '(': raise JOPAException('No (')
        b = 1
        while b or self.string is None:
            c = self.getchar()
            if c is None: raise JOPAException('Unbalanced braces')
            if c == '(': b += 1
            if c == ')': b -= 1
        self.string = self.string[:-1]
        return self

    def eval(self):
        """ Eagerly evaluates with every single incoming byte """
        if not self.string is None:
            self.source = Source('(' + self.string + ')')
            self.string = None
        if not self.source() == '(': raise JOPAException('No (')
        f = self.read_one()
        if f is None: return JOPAObjectNone(self) # ()
        if isinstance(f, str):
            if f in self: f = self[f]
            else: raise JOPAException("Uncallable '%s' begins the brace" % f)
        if isinstance(f, JOPABrace): f = f.eval()
        self.exposed_current_state = f
        while True:
            if isinstance(f, str): f = JOPABrace(f, self)
            if isinstance(f, JOPABrace): f = f.eval()
            self.exposed_current_state = f
            a = self.read_one(eager=(not f.takes_literal))
            if a is None: break
            f = self.apply(f, a)
        return f

    def read_one(self, eager=True):
        s = ''
        while self.source.peek().isspace(): self.getchar()
        if self.source.peek() == ')': self.source(); return None
        while True:
            c = self.source.peek()
            if not c: raise JOPAException('Premature end of source')
            if c == '(':
                new = JOPABrace(self.source, self)
                self.exposed_current_state = new
                if eager: new._suckup()
                return new
            elif c.isspace(): break;
            elif c == ')': break;
            else: s += self.getchar()
        return s if len(s) else None

    def getchar(self):
        if self.string is None: self.string = ''
        char = self.source()
        if not char is None: self.string += char
        return char

    def apply(self, f, a):
        #print 'APPLY "%s" "%s"' % (f, a), f.takes_literal, type(a)
        if f.takes_literal:
            if isinstance(a, str): return f(JOPAString(a), self)
            if isinstance(a, JOPABrace): return f(a._suckup(), self)
            raise JOPAException("Unknown argument type for function of literal")
        else:
            if isinstance(a, str):
                if a in self: a = self[a]
            elif isinstance(a, JOPABrace):
                a.parent = self
                a = a.eval()
        return f(a, self)

    def __call__(self, arg, brace):
        return self.apply(self.eval_eager(), arg)

    def __str__(self): return self.string

### Utility decorators for defining python functions

def jopa_function(fname, takes_literal=False, auto_add=False):
    def transform(f_outer):
        f = f_outer
        while '_inner_func' in f.__dict__:
            f = f._inner_func
        f.takes_literal = takes_literal
        f.__str__ = types.MethodType((lambda s: fname), f, f.__class__)
        if auto_add: # automatically add it into packages inside jopa_ro
            name = fname
            assert name.startswith('jopa.'); name = name.split('.', 1)[1]
            pkg = jopa_ro
            while '.' in name:
                prefix, name = name.split('.', 1)
                pkg = pkg.dic[prefix]
            pkg.dic[name] = f_outer
        return f_outer
    return transform

def takes_additional_arg(argname, literal=False, verificator=None):
    def transform(func):
        @jopa_function(str(func), takes_literal=literal)
        def PartiallyApplied(addn_arg, brace, **more_args):
            if verificator is not None:
                r = verificator(addn_arg)
                if not r == True: raise JOPAException(r)
            @jopa_function(str(func), takes_literal=func.takes_literal)
            def ProxyFunc(arg, brace, *args, **kwargs):
                kwargs[argname] = addn_arg
                kwargs.update(more_args)
                return func(arg, brace, *args, **kwargs)
            return ProxyFunc
        PartiallyApplied._inner_func = func
        return PartiallyApplied
    return transform

isstring = lambda s: isinstance (s, JOPAString) or 'argument is not a string'

### Standard library ###

@jopa_function('jopa.context.get', auto_add=True)
def JOPAContextGet(arg, brace):
    if not isinstance(arg, JOPAString):
        raise JOPAException('jopa.context.get requires a string')
    return brace[str(arg)]

@jopa_function('jopa.context.set', auto_add=True)
@takes_additional_arg('valname', literal=True)
def JOPAContextSet(arg, brace, valname=None):
    brace.context[str(valname)] = arg
    return JOPAIdent

@jopa_function('jopa.operator.ident', auto_add=True)
def JOPAIdent(arg, brace): return arg

@jopa_function('jopa.operator.ignore', auto_add=True)
def JOPAIgnore(arg, brace): return JOPAIdent

@jopa_function('jopa.operator.ternary', auto_add=True)
def JOPATernary(arg, brace):
    if not isinstance(arg, JOPABoolean):
        raise JOPAException('Non-bool condition')
    if isinstance(arg, JOPATrue):
        return JOPAEvalNthLiteral(1, 2)
    else:
        return JOPAEvalNthLiteral(2, 2)

class JOPAEvalNthLiteral(JOPAObject):
    def __init__(self, n, all, i=None, answer=None):
        JOPAObject.__init__(self, takes_literal=True)
        if i is None: i = 1
        self.i, self.n, self.all, self.answer = i, n, all, answer
    def __call__(self, arg, brace):
        if self.n == self.i:
            self.answer = arg.eval()
        if self.i == self.all:
            assert(not self.answer is None)
            return self.answer
        return JOPAEvalNthLiteral(self.n, self.all, self.i + 1, self.answer)

@jopa_function('jopa.function.of', auto_add=True)
@takes_additional_arg('argname', literal=True)
@takes_additional_arg('function', literal=True)
def JOPAFunctionOf(arg, brace, function=None, argname=None):
        function.context[str(argname)] = arg
        return function.eval()

@jopa_function('jopa.string.equal', auto_add=True)
@takes_additional_arg('string1', verificator=isstring)
def JOPAStringEqual(string2, brace, string1):
    if not isinstance(string2, JOPAString):
        raise JOPAException('jopa.string.equal requires 2nd string')
    return JOPABool(str(string1) == str(string2))

@jopa_function('jopa.operator.uncallable', auto_add=True)
def JOPAUncallable(arg, brace):
    raise JOPAException('uncallable was called with "%s"' % str(arg))

@jopa_function('jopa.string.surround', auto_add=True)
@takes_additional_arg('surr', verificator=isstring)
def JOPAStringSurround(arg, brace, surr=None):
    return JOPAString(str(surr) + str(arg) + str(surr))


def main(): print JOPABrace(raw_input, rootobj=jopa_ro).eval()
if __name__ == '__main__': main()

