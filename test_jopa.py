#!/usr/bin/python

# an eXtensible Syntax LANGuage experiment - Joys Of Partial Application Tests
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

from jopa import simple_eval

TESTS = (
    ("(jopa string create Hello, (jopa string space) world!)", "Hello, world!"),
    ("(jopa string literal (Hello, world!))",                  "Hello, world!"),
    ("(jopa string literal (\t))",                             "\t"),
    ("(jopa string create a (jopa string tab) b)",             "a\tb"),
    ("(jopa context get (jopa string literal (jopa)))",
     'jopa root package'),
    ("(jopa context set hi (jopa string literal (Hello)) hi)", 'Hello'),
    ("(jopa operator ident jopa)",
     'jopa root package'),
    ("""(jopa string equal
         (jopa string literal hi)
         (jopa string literal (hi))
        )""", "true"),
    ("""(jopa string equal
         (jopa string literal)
         (jopa string literal ())
        )""", "true"),
    ("""(jopa string equal
         (jopa string create ())
         (jopa string literal ())
        )""", "false"),
    ("""(jopa string create
         (jopa string lbrace)
         hi
         (jopa string rbrace)
        )""", "(hi)"),
    ("""(jopa context set x (jopa string literal hello)
         jopa context set y (jopa string literal world)
         jopa string create x y)""", "helloworld"),
)

if __name__ == '__main__':
    for c, r in TESTS:
        e = simple_eval(c, eager=True)
        ee = simple_eval(c, eager=False)
        if not (str(ee) == r and str(e) == r):
            print 'A test failed:            ', c
            print 'Evaluation returned:      ', e
            print 'Eager evaluation returned:', ee
            print 'Expected:                 ', r

