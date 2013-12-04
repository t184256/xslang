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

#class XCallable(XObject): pass
class XUncallable(XObject):
    def __str__(self):
        raise XException('Uncallable ' + XObject.__str__(self) + ' called')
#
## TODO: implement primitive types in xslang
#class XBoolean(XUncallable):
#    @staticmethod
#    def convert(obj): return XTrue() if obj else XFalse()
#class XTrue(XBoolean): pass
#class XFalse(XBoolean): pass
class XNone(XUncallable): pass

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
    s = ''
    while True:
        s += stream.next()
        if s[-1] in '()' or s[-1].isspace(): yield s[:-1]; yield s[-1]; s = ''


### The interpreter ###

class XInterpreter(object):
    def __init__(self, stream, root_obj=None, root_obj_name='xslang', \
                no_first_brace=False, parent=None):
        self.context = {root_obj_name: root_obj or xslang_ro}
        self.stream = stream_str(stream) if isinstance(stream, str) else stream
        self.parent = parent
        self.no_first_brace = no_first_brace

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
        self.token_stream = stream_read_word_or_brace(self.stream)
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
            if f is None: f = n
            else: f = f(n, interpreter=self)
            while 'init' in dir(f):
                print 'before init', f
                f = f.init(interpreter=self)
                print 'after init', f
            
    def apply(f, n):
        return f(n, self)

def Xident(arg, interpreter): return arg
def Xignore(arg, interpreter): return Xident
class XLiteral(XObject):
    def init(arg, interpreter):
        self.s = stream_read_until_closing_brace(interpreter.source, 0)
        return self.s
    def __call__(arg, interpreter):
        raise XException('Attempted to call a literal ' + self.s)

def steal_literal(interpreter):
    s = ''
    while not s or s.isspace(): s = interpreter.token_stream.next()
    if s == '(': return stream_read_until_closing_brace(interpreter.stream)
    return s

class XDictionaryObject(XObject, dict):
    def init(self, interpreter):
        return self[steal_literal(interpreter).strip()]
    def __call__(self, arg, interpreter):
        return self[arg]

xslang_rootobj = XDictionaryObject({
    'operators': XDictionaryObject({
        'ident': Xident,
        'ignore': Xignore,
    }),
})

def main():
    print XInterpreter('(xslang operators ident)', xslang_rootobj).eval()
    print XInterpreter('(xslang (operators) ident)', xslang_rootobj).eval()

if __name__ == '__main__': main()
