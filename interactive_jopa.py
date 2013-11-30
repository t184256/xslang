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

from jopa import JOPABrace, JOPAString, JOPAObjectPackage, CollectArgs
from jopa import jopa_ro

import sys, time, re

ugly_objectdesc = re.compile(r'<(\S*) object at .*>')

class BackspaceException(Exception): pass
class EnterException(Exception): pass
class TabException(Exception): pass

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
        self.b.eval()

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
            state = prettyprintstate(self.b)
            l = 80 - (len(self.prompt()) + len(wrote) + len(state))
            if l > 0:
                print self.prompt() + wrote + ' ' * l + state
            else:
                print; print state
                print; print self.prompt() + wrote
                print; print
            self.interpreter_got_recreated = False
            c = getch()
            if ord(c) == 9: raise TabException()
            if ord(c) == 13: raise EnterException()
            if ord(c) == 27: sys.exit(0)
            if ord(c) == 127: raise BackspaceException()
            out = self.s
            self.h += out
            self.s = c
#           print "$ '%s' | '%s'" % (self.h, self.s)
            return out

def shorten(s, maxlen):
    s = str(s)
    if len(s) <= maxlen: return s
    return s[:maxlen - 3] + '..' + s[-1]

def prettyprintstate(b):
    state = b.exposed_current_state
    if isinstance(state, JOPABrace):
        return '(' + shorten(prettyprintstate(state), 40) + ')'
    if isinstance(state, JOPAString): return '\'' + shorten(state, 40) + '\''
    if isinstance(state, CollectArgs):
        return str(state) + ' ' + ' '.join([
                shorten(argname, 10) + '=(' + shorten(val, 16) + ')'
                for argname, val in state.args.items()])
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
        except TabException, e:
            s = i.h + i.s
            choices = i.b.context.keys()
            if isinstance(i.b.exposed_current_state, JOPAObjectPackage):
                choices = i.b.exposed_current_state.dic.keys() + choices
            prefix = s.split()[-1].split('(')[-1].split(')')[-1]
            filtered = [c for c in choices if c.startswith(prefix)]
            if len(filtered) == 1:
                s += filtered[0][len(prefix):] + ' '
            else:
                print ' '.join(choices)
        except EnterException, e: s = INITIAL_S
        except Exception, e:
            print 'E', type(e), e.message
            s = i.h

if __name__ == '__main__': main()

