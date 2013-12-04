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

from xslang import XInterpreter, XException, XDictionaryObject

import sys, time, re, traceback

# TODO: remove
ugly_objectdesc = re.compile(r'<(\S*) object at .*>')

class BackspaceException(Exception): pass
class ControlWException(Exception): pass
class EnterException(Exception): pass
class TabException(Exception): pass

# TODO: compact
try:
    from msvcrt import getch
except ImportError:
    def getch():
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# TODO: rewrite as a generator
class Interactive(object):
    def __init__(self, initial_string=None):
        self.s = initial_string
        self.h = ''
        self.interpreter_got_recreated = True # alters the prompt to !
        self.subsource = getch
        self.xi = XInterpreter(self)
        self.display_error = None

    def main(self):
        self.xi.eval()

    def prompt(self): return '! ' if self.interpreter_got_recreated else '> '

    def next(self):
        if self.s:
            self.h, c, self.s = self.h + self.s[0], self.s[0], self.s[1:]
            return c
# TODO: print only in printstate
        print '\n' * 24
        printstate(self.xi)
        if self.display_error is None:
            print '\n' * 2
        else:
            print '\n' + self.display_error + '\n'
        print self.prompt() + self.h + '#'
        self.interpreter_got_recreated = False
        self.display_error = None
        c = self.subsource()
        if ord(c) == 9: raise TabException()
        if ord(c) == 23: raise ControlWException()
        if ord(c) == 13: raise EnterException()
        if ord(c) == 27: sys.exit(0)
        if ord(c) == 127: raise BackspaceException()
        self.h += c
        return c

def shorten(s, maxlen):
    s = str(s)
    if len(s) <= maxlen: return s
    return s[:maxlen - 3] + '..' + s[-1]

def printstate(b, shorten_to=80, stars=1):
    for f in b.previous + [b.currently_mutating]:
        if isinstance(f, XInterpreter):
            printstate(f, shorten_to, stars=1)
        s = str(f)
        if not s: s = '...'
        symbol = '*' if f != b.currently_mutating else '.'
        print symbol * stars, shorten(s, shorten_to - stars - 1)
#    print '.' * stars, b.currently_mutating

INITIAL_S = '('

def main():
    s = INITIAL_S if len(sys.argv) < 2 else INITIAL_S + ' '.join(sys.argv[1:])
    display_error = None
    while True:
        try:
            i = Interactive(s)
            i.display_error = display_error
            i.main()
        except BackspaceException, e:
            s = i.h[:-1]
            display_error = None
        except ControlWException, e:
            s = i.h.rstrip().rsplit(' ', 1)[0] + ' '
            display_error = None
        except TabException, e:
            display_error = None
            s = i.h
            choices = i.xi.context.keys()
            curr = None
            if i.xi.previous: curr = i.xi.previous[:-1]
            if i.xi.currently_mutating: curr = i.xi.currently_mutating
            while isinstance(curr, XInterpreter):
                if not curr.currently_mutating is None:
                    curr = curr.currently_mutating; continue
            if curr:
                if isinstance(curr, XDictionaryObject):
                    choices = curr.keys() + choices
            prefix = s.split()[-1].split('(')[-1].split(')')[-1]
            filtered = [c for c in choices if c.startswith(prefix)]
            if len(filtered) == 1:
                s += filtered[0][len(prefix):] + ' '
            else:
                display_error = ': ' + ' '.join(sorted(choices))
        except EnterException, e:
            display_error = None
            s = INITIAL_S
        except XException, e:
            display_error = 'X ' + str(e)
            s = i.h[:-1]
        except Exception, e:
            display_error = 'E ' + str(e)
            s = i.h[:-1]

if __name__ == '__main__': main()

