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

class JOPAObject(object):
    def __init__(self, takes_literal=False):
        self.takes_literal = takes_literal

### The interpreter: the Brace ###

class JOPARuntimeException(Exception): pass

class StringSource(object):
    def __init__(self, code):
        self._str = code
    def peek(self):
        if not self._str: return None
        return self._str[0]
    def __call__(self):
        if not self._str: return None
        char = self._str[0]
        self._str = self._str[1:]
        return char

class JOPABrace(JOPAObject):
    def __init__(self, source, parent=None, rootobj=None):
        if isinstance(source, str): source = StringSource(source)
        self.source = source
        self.context = {}
        if not rootobj is None: self.context['jopa'] = rootobj
        self.parent = parent
        self.string = ''
        self.exposed_current_state = None

    def __getitem__(self, n, maxdepth=-1):
        if n in self.context: return self.context[n]
        if not self.parent: raise Exception(n + ' not found!')
        if maxdepth == 0: raise Exception(n + ' not found here!')
        return self.parent.__getitem__(n, maxdepth - 1)

    def __contains__(self, n):
        if n in self.context: return True
        if not self.parent: return False
        return n in self.parent

    def _parse(self):
        """ Parses '(x y z) coming from source into a stored list [x, y, z] """
        if '_parsed' in self.__dict__: return self
        self._parsed = []
        if not self.source() == '(': raise Exception('No (')
        f = self.read_one()
        if f is None: return self
        if isinstance(f, JOPABrace): f = f._parse()
        self._parsed.append(f)
        while True:
            a = self.read_one()
            if isinstance(a, JOPABrace): a._parse()
            if a is None: break
            self._parsed.append(a)
        return self

    def eval(self):
        """ Parses, then evaluates the brace, feeding the arguments into the
        first one """
        if not '_parsed' in self.__dict__: self._parse()
        if not len(self._parsed): return JOPAObjectNone(self) # ()
        f = self._parsed[0]
        if isinstance(f, JOPABrace): f = f.eval()
        if isinstance(f, str):
            if f in self: f = self[f]
            else:
                raise Exception("Uncallable literal '%s' starts the brace" % f)
        for a in self._parsed[1:]:
            f = self.apply(f, a)
        return f

    def eval_eager(self):
        """ Eagerly evaluates with every single incoming byte """
        if '_parsed' in self.__dict__: return self.eval()
        if not self.source() == '(': raise Exception('No (')
        f = self.read_one()
        if f is None: return JOPAObjectNone(self) # ()
        if isinstance(f, JOPABrace): f = f.eval_eager()
        if isinstance(f, str):
            if f in self: f = self[f]
            else:
                raise Exception("Uncallable literal '%s' starts the brace" % f)
        self.exposed_current_state = f
        while True:
            a = self.read_one()
            if a is None: break
            f = self.apply(f, a)
            self.exposed_current_state = f
        return f

    def read_one(self):
        s = ''
        while self.source.peek().isspace(): self.getchar()
        if self.source.peek() == ')': self.source(); return None
        while True:
            c = self.source.peek()
            if not c: raise Exception('Premature end of source')
            if c == '(':
                new = JOPABrace(self.source, self)
                self.exposed_current_state = new
                return new
            elif c.isspace(): break;
            elif c == ')': break;
            else:
                s += self.getchar()
        return s if len(s) else None

    def getchar(self):
        char = self.source()
        self.string += char
        return char

    def apply(self, f, a):
        #print 'APPLY "%s" "%s"' % (f, a), f.takes_literal, type(a)
        if f.takes_literal:
            if isinstance(a, str): return f(JOPAString(a), self)
            if isinstance(a, JOPABrace): return f(a._parse(), self)
            raise Exception("Unknown argument type for function of literal")
        else:
            if isinstance(a, str):
                if a in self:
                    a = self[a]
            if isinstance(a, JOPABrace):
                if f.takes_literal:
                    a = a._parse()
                else:
                    a.parent = self
                    a = a.eval_eager()
        return f(a, self)

    def __call__(self, arg, brace):
        return self.apply(self.eval_eager(), arg)

    def __str__(self): return self.string

### Standard library ###

class JOPAObjectNone(JOPAObject): pass

class JOPAObjectPackage(JOPAObject):
    def __init__(self, name, dic):
        JOPAObject.__init__(self)
        self.dic, self.name = dic, name
    def __call__(self, arg, brace):
        return self.dic[arg]
    def __str__(self):
        return self.name

class JOPAString(JOPAObject):
    def __init__(self, initial_string=None, takes_literal=False):
        JOPAObject.__init__(self, takes_literal=takes_literal)
        self._str = initial_string or ''
    def __call__(self, arg, brace):
        return JOPAString(initial_string=(self._str + str(arg)))
    def __str__(self):
        return self._str

class JOPAContextGet(JOPAObject):
    def __call__(self, arg, brace):
        if not isinstance(arg, JOPAString):
            raise Exception('jopa.context.get requires a string')
        return brace[str(arg)]

class JOPAContextSetCreator(JOPAObject):
    def __init__(self):
        JOPAObject.__init__(self, takes_literal=True)
    def __call__(self, arg, brace):
        return JOPAContextSet(str(arg))

class JOPAContextSet(JOPAObject):
    def __init__(self, name):
        JOPAObject.__init__(self)
        self.name = name
    def __call__(self, arg, brace):
        brace.context[self.name] = arg
        return JOPAIdent()

class JOPAIdent(JOPAObject):
    def __call__(self, arg, brace):
        return arg

class JOPABoolean(JOPAObject): pass
class JOPATrue(JOPABoolean):
    def __str__(self): return 'true'
class JOPAFalse(JOPABoolean):
    def __str__(self): return 'false'
def JOPABool(obj): return JOPATrue() if obj else JOPAFalse()

class JOPAStringEqualCreator(JOPAObject):
    def __call__(self, arg, brace):
        if not isinstance(arg, JOPAString):
            raise JOPARuntimeException('jopa.string.equal requires 1st string')
        return JOPAStringEqual(arg)

class JOPAStringEqual(JOPAObject):
    def __init__(self, s):
        JOPAObject.__init__(self)
        self._s = s
    def __call__(self, arg, brace):
        if not isinstance(arg, JOPAString):
            raise JOPARuntimeException('jopa.string.equal requires 2nd string')
        return JOPABool(str(self._s) == str(arg))

jopa_ro = JOPAObjectPackage('jopa root package', {
    'operator': JOPAObjectPackage('jopa.operator package', {
        'ident': JOPAIdent(),
    }),
    'context': JOPAObjectPackage('jopa.context package', {
        'get': JOPAContextGet(),
        'set': JOPAContextSetCreator(),
    }),
    'bool': JOPAObjectPackage('jopa.bool package', {
        'true': JOPATrue(),
        'false': JOPAFalse(),
    }),
    'string': JOPAObjectPackage('jopa.string package', {
        'create': JOPAString(),
        'literal': JOPAString(takes_literal=True),
        'equal': JOPAStringEqualCreator(),
        'lbrace': JOPAString('('),
        'rbrace': JOPAString(')'),
        'space': JOPAString(' '),
        'tab': JOPAString('\t'),
        'newline': JOPAString('\n'),
    })
})

### External interface ###

def simple_eval(code, eager=True):
    b = JOPABrace(code, rootobj=jopa_ro)
    if eager:
        return b.eval_eager()
    else:
        return b.eval()

def main():
    print simple_eval(raw_input())

if __name__ == '__main__': main()

