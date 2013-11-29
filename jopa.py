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

### The interpreter: the Brace ###

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
    def preview(self): return self._str

class JOPABrace(JOPAObject):
    def __init__(self, source, parent=None, rootobj=None):
        self.source = source
        self.context = {}
        if not rootobj is None: self.context['jopa'] = rootobj
        self.parent = parent
        self.string = ''

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
        for a in self._parsed[1:]:
            if isinstance(a, JOPABrace):
                if f.takes_literal:
                    a = a._parse()
                else:
                    a = a.eval()
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
        while True:
            a = self.read_one()
            if a is None: break
            if isinstance(a, JOPABrace):
                if f.takes_literal:
                    a = a._parse()
                else:
                    a = a.eval_eager()
#                a = a.eval_eager() if f.takes_literal else a._parse()
            f = self.apply(f, a)
        return f

    def read_one(self):
        s = ''
        while self.source.peek().isspace(): self.getchar()
        if self.source.peek() == ')': self.source(); return None
        while True:
            c = self.source.peek()
            if not c: raise Exception('Premature end of source')
            if c == '(':
                return JOPABrace(self.source, self)
            elif c.isspace(): break;
            elif c == ')': break;
            else:
                s += self.getchar()
        return s if len(s) else None

    def getchar(self):
        char = self.source()
        self.string += char
        return char

    def apply(self, func, arg):
        if func.takes_literal:
            if isinstance(arg, str): return func(JOPAString(arg), self)
            if isinstance(arg, JOPABrace): return func(arg._parse(), self)
            raise Exception("Unknown argument type for function of literal")
        return func(arg, self)

    def __call__(self, arg, brace):
        return self.apply(self.eval_eager(), arg)

    def __str__(self): return self.string

jopa_ro = JOPAObjectPackage('jopa root package', {
    'string': JOPAObjectPackage('jopa.string package', {
        'create': JOPAString(),
        'space': JOPAString(' '),
        'literal': JOPAString(takes_literal=True),
    })
})

#code = "(func1 arg1 (func2 arg2) () arg3 (func3 ()))"
code = "(jopa string create Hello, (jopa string space) world!)"
code = "(jopa string literal (Hello, world))"
ss = StringSource(code)

print 'parse'
print JOPABrace(StringSource(code), rootobj=jopa_ro)._parse()._parsed
print

print 'eval'
print JOPABrace(StringSource(code), rootobj=jopa_ro).eval()
print

print 'eval_eager'
print JOPABrace(StringSource(code), rootobj=jopa_ro).eval_eager()
print

