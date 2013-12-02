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

from jopa import JOPABrace, JOPAString, JOPAObjectPackage, Source
from jopa import JOPAException

import sys, time, re, traceback

ugly_objectdesc = re.compile(r'<(\S*) object at .*>')

class BackspaceException(Exception): pass
class ControlWException(Exception): pass
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

# TODO rewrite for the new Source
class Interactive(object):
    def __init__(self, initial_string=None):
        self.s = initial_string
        self.h = ''
        self.interpreter_got_recreated = True # alters the prompt to !
        self.subsource = getch
        self.b = JOPABrace(Source(subsource=self))

    def main(self):
        self.b.eval()

    def prompt(self): return '! ' if self.interpreter_got_recreated else '> '

    def __call__(self):
        if self.s:
            self.h, c, self.s = self.h + self.s[0], self.s[0], self.s[1:]
            return c
        state = prettyprintstate(self.b, shorten_to=30)
        l = 80 - (len(self.prompt()) + len(self.h) + len(state) + 1)
        if l > 0:
            print self.prompt() + self.h + '#' + ' ' * l + state
        else:
            state = prettyprintstate(self.b, shorten_to=78)
            print '->' + state
            print self.prompt() + self.h + '#'
        self.interpreter_got_recreated = False
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

def prettyprintstate(b, shorten_to=78):
    state = b.exposed_current_state
    if isinstance(state, JOPABrace):
        return '(' + shorten(prettyprintstate(state), shorten_to) + ')'
    if isinstance(state, JOPAString):
        return '\'' + shorten(state, shorten_to) + '\''
    if not state: return '...'
    m = ugly_objectdesc.match(str(state))
    if m: return m.group(1)
    return str(state)# + ' ' + str(type(state))

INITIAL_S = '('

def main():
    s = INITIAL_S if len(sys.argv) < 2 else INITIAL_S + ' '.join(sys.argv[1:])
    while True:
        try:
            i = Interactive(s)
            i.main()
        except BackspaceException, e: s = i.h[:-1]
        except ControlWException, e: s = i.h.rstrip().rsplit(' ', 1)[0] + ' '
        except TabException, e:
            s = i.h
            choices = i.b.context.keys()
            if isinstance(i.b.exposed_current_state, JOPAObjectPackage):
                choices = i.b.exposed_current_state.dic.keys() + choices
            prefix = s.split()[-1].split('(')[-1].split(')')[-1]
            filtered = [c for c in choices if c.startswith(prefix)]
            if len(filtered) == 1:
                s += filtered[0][len(prefix):] + ' '
            else:
                print ': ' + ' '.join(choices)
        except EnterException, e: s = INITIAL_S
        except JOPAException, e:
            print 'E', e
            s = i.h[:-1]
        except Exception, e:
            print 'E', traceback.format_exc(e)
            s = i.h[:-1]

if __name__ == '__main__': main()

