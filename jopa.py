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

class JOPAInterpreter(object):
    def __init__(self, source, parent=None, rootobj=None):
        self.source = source
        self.context = {}
        if not rootobj is None: self.context['jopa'] = rootobj
        self.parent = parent

    def __getitem__(self, n, maxdepth=-1):
        if n in self.context: return self.context[n]
        if not self.parent: raise Exception(n + ' not found!')
        if maxdepth == 0: raise Exception(n + ' not found here!')
        return self.parent.__getitem__(n, maxdepth - 1)

    def __contains__(self, n):
        if n in self.context: return True
        if not self.parent: return False
        return n in self.parent

    def interpret(self):
        if not self.source() == '(': raise Exception('No (')
        o = self.read_one()
        if o is None: return JOPAObjectNone(self) # ()
        if o in self: o = self[o]
        while True:
            arg = self.read_one()
            if arg is None: break
            o = o(arg, self) # Provide a less eager evaluation later
        return o

    def read_one(self):
        s = ''
        while self.source.peek().isspace(): self.source()
        if self.source.peek() == ')': self.source(); return None
        while True:
            c = self.source.peek()
            if not c: raise Exception('Premature end of source')
            if c == '(':
                return JOPAInterpreter(self.source, self).interpret()
            elif c.isspace(): break;
            elif c == ')': break;
            else:
                s += self.source()
        return s or None

class JOPAObject(object): pass
class JOPAObjectNone(JOPAObject): pass

class JOPAObjectPackage(JOPAObject):
    def __init__(self, name, dic):
        self.dic, self.name = dic, name
    def __call__(self, arg, interpreter):
        return self.dic[arg]
    def __str__(self):
        return self.name
class JOPAStringCreate(JOPAObject):
    def __init__(self, initial_string=None):
        self._str = initial_string or ''
    def __call__(self, arg, interpreter):
        return JOPAStringCreate(initial_string=(self._str + str(arg)))
    def __str__(self):
        return self._str
jopa_ro = JOPAObjectPackage('jopa root package', {
    'string': JOPAObjectPackage('jopa.string package', {
        'create': JOPAStringCreate(),
        'space': JOPAStringCreate(' '),
    })
})

#code = "(func1 arg1 (func2 arg2) () arg3 (func3 ()))"
code = "(jopa string create Hello, (jopa string space) world!)"
ss = StringSource(code)

print JOPAInterpreter(ss, rootobj=jopa_ro).interpret()


