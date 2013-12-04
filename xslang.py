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

## TODO: implement primitive types in xslang
#class XBoolean(XObject):
#    @staticmethod
#    def convert(obj): return XTrue() if obj else XFalse()
#class XTrue(XBoolean): pass
#class XFalse(XBoolean): pass
class XNone(XObject): pass

### Streaming ###

def stream_str(string):
    while True:
        c, string = string[0], string[1:]
        yield c
        if not string: return

def stream_read_until_closing_brace(stream, opened=1):
    s, b = '', opened
    while b > 0 or not ('(' in s or ')' in s):
        c = stream.next(); s += c
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
        s += stream.next()
        if s:
            if s[-1] == '(' or s[-1].isspace():
                if s[:-1]: yield s[:-1]
                yield s[-1]; s = ''
        if s:
            if s[-1] == ')': yield s[:-1]; yield ''; yield s[-1]; s = ''


### The interpreter ###

class XInterpreter(object):
    def __init__(self, stream, root_obj=None, root_obj_name='xslang', \
                no_first_brace=False, parent=None):
        self.context = {root_obj_name: root_obj or xslang_rootobj}
        self.stream = stream_str(stream) if isinstance(stream, str) else stream
        self.token_stream = stream_read_word_or_brace(self.stream)
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
           if self.stream.next() != '(': raise XException('No (')
        f = None
        while True:
            n = self.token_stream.next()
            if n.isspace() or n == '': continue
            elif n == '(':
                n = XInterpreter(self.stream, no_first_brace=True, parent=self)
                n = n.eval()
            elif n == ')': return f
            if (isinstance(n, str)):
                if n in self: n = self[n]
                else: raise XException('No ' + n + ' in current context!')
            if f is None: f = n
            else: f = f(n, interpreter=self)
            assert isinstance(f, XObject)
            while 'init' in dir(f):
                self.currently_mutating = f
                transformed = f.init(interpreter=self)
                #print f, 'TRANSFORMED INTO', transformed
                if transformed is None: break # Cancel transformation
                else: f = transformed
                assert isinstance(f, XObject)
            self.previous.append(f)

    def apply(f, n):
        return f(n, self)

### Helper decorators for standard library ###

def steal_literal(interpreter):
    s = ''
    while not s or s.isspace():
        s = interpreter.token_stream.next()
        if not s: return None
    if s == '(': return stream_read_until_closing_brace(interpreter.stream)
    return s

def XFunction(name=None, initializer=None):
    def transform(func):
        class XFunc(XObject):
            def init(self, *a, **kwa):
                return initializer(*a, **kwa) if initializer else None
            def __call__(self, *a, **kwa):
                return func(*a, **kwa)
            def __str__(self): return 'X<' + name + '>' \
                    if name is not None else XObject.__str__(self)
        return XFunc()
    return transform

def XFunction_takes_additional_literal(literal_name):
    def transform(func):
        class XMutantConsumingALiteral(XObject):
            def __init__(self, literal=None):
                self._literal = literal
            def init(self, interpreter):
                l = self._literal
                @XFunction('LiteralInjector %s="%s" -> %s' %
                           (literal_name, l, str(func)))
                def XLiteralInjector(*a, **kwa):
                    kwa[literal_name] = l
                    return func(*a, **kwa)
                if not l is None: return XLiteralInjector
                l = steal_literal(interpreter)
                if l: return Xsetlit(literal = l)
                return self
            __str__ = lambda s: 'X<MutantConsumingALiteral to %s>' % str(func)
        return XMutantConsumingALiteral
    return transform

def XFunction_takes_additional_argument(arg_name, convertor=None):
    def transform(func):
        @XFunction('ArgInjector %s -> %s' % (arg_name, str(func)))
        def XArgInjector(arg, interpreter, **kwa_):
            arg = convertor(arg)
            @XFunction('ArgInjector %s=(%s) -> %s' % (arg_name, arg, str(func)))
            def ProxyFunc(*a, **kwa):
                kwa.update(kwa_)
                kwa[arg_name] = arg
                return func(*a, **kwa)
            return ProxyFunc
        return XArgInjector
    return transform

def Xc_tostr(s):
    if isinstance(s, Xstring): return s.str()
    raise XException('Not an Xstring: ' + str(s))

### Standard library ###

@XFunction('ident')
def Xident(arg, interpreter): return arg
@XFunction('ignore')
def Xignore(arg, interpreter): return Xident

class XDictionaryObject(XObject, dict):
    def init(self, interpreter):
        l = steal_literal(interpreter)
        if not l: return
        return self[l]

class Xstring(XDictionaryObject):
    def __init__(self, s): self._s = s
    def __str__(self): return 'X<\'' + self._s + '\'>'
    def str(self): return self._s

class XstringLiteralCreator(XObject):
    def init(self, interpreter):
        l = steal_literal(interpreter)
        return Xstring(l)

@XFunction('setlit')
@XFunction_takes_additional_literal('varname')
def Xsetlit(arg, interpreter, varname=None):
    interpreter.context[varname] = arg
    return Xident

@XFunction('set')
@XFunction_takes_additional_argument('varname', convertor=Xc_tostr)
def Xset(arg, interpreter, varname=None):
    interpreter.context[varname] = arg
    return Xident


xslang_rootobj = XDictionaryObject({
    'context': XDictionaryObject({
        'set': Xset,
        'setlit': Xsetlit(),
    }),
    'operator': XDictionaryObject({
        'ident': Xident,
        'ignore': Xignore,
        'literal': XstringLiteralCreator(),
    }),
})

if __name__ == '__main__': print XInterpreter(raw_input()).eval()
