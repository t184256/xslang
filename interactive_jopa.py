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

from jopa import JOPABrace, JOPAString, jopa_ro

import sys, time, re

ugly_objectdesc = re.compile(r'<(\S*) object at .*>')

class BackspaceException(Exception): pass
class EnterException(Exception): pass

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

class Interactive(object):
    def __init__(self, initial_string=None):
        self.s = initial_string or '('
        self.b = JOPABrace(self, rootobj=jopa_ro)
        self.h = ''
        self.interpreter_got_recreated = True # alters the prompt to !

    def prompt(self): return '! ' if self.interpreter_got_recreated else '> '

    def main(self):
        self.b.eval_eager()

    def peek(self):
        return self.s[0]

    def __call__(self):
        if len(self.s) > 1:
            c = self.s[0]
            self.s = self.s[1:]
            self.h += c
            return c
        else:
            wrote = self.h + self.s
            state = prettyprint(self.b.exposed_current_state, self.b)
            l = 80 - (len(self.prompt()) + len(wrote) + len(state))
            if l > 0:
                print self.prompt() + wrote + ' ' * l + state
            else:
                print self.prompt() + wrote
                print state
            self.interpreter_got_recreated = False
            c = getch()
            if ord(c) == 13: raise EnterException()
            if ord(c) == 27: sys.exit(0)
            if ord(c) == 127: raise BackspaceException()
            out = self.s
            self.h += out
            self.s = c
#           print "$ '%s' | '%s'" % (self.h, self.s)
            return out

def prettyprint(state, b):
    print b
    if isinstance(state, JOPABrace):
        return '(' + prettyprint(state.exposed_current_state, state) + ')'
    if isinstance(state, JOPAString): return '\'' + str(state) + '\''
    if not state: return '...'
    m = ugly_objectdesc.match(str(state))
    if m: return m.group(1)
    return str(state)# + ' ' + str(type(state))

INITIAL_S = '('

def main():
    s = INITIAL_S
    while True:
        try:
            i = Interactive(s)
            i.main()
        except BackspaceException, e: s = i.h
        except EnterException, e: s = INITIAL_S
        except Exception, e:
            print 'E', type(e), e.message
            s = i.h

if __name__ == '__main__': main()

