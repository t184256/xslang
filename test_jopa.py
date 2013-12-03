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

from jopa import JOPABrace
import traceback

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
    ("(jopa operator ignore jopa jopa)",
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
    ("""(jopa operator ternary (jopa bool false)
         (an erroroneous code) (jopa string create fl))""",  "fl"),
    ("""(jopa operator ternary (jopa bool true)
         (jopa string create tr) (an erroroneous code))""",  "tr"),
    ("""(jopa operator ternary (jopa bool false)
         (jopa operator uncallable jopa) (jopa string create fl))""",  "fl"),
    ("""(jopa operator ternary (jopa bool true)
         (jopa string create tr) (jopa operator uncallable jopa))""",  "tr"),
    ("(jopa string literal (jopa operator uncallable jopa))",
     "jopa operator uncallable jopa"),
    ("""(jopa operator ternary
           (jopa string equal (jopa string create hi) (jopa string literal hi))
         (jopa string create tr) (an erroroneous code))""",  "tr"),
    ("(jopa function of x (jopa string create oh x !) dear)","ohdear!"),
    ("""(jopa context set cc
         (jopa function of x
          (jopa function of y
           (jopa string create a x b y c)
          )
         )
        cc (jopa string create 1) (jopa string create 2))""","a1b2c"),
    ("(jopa syntax enable square_brackets jopa string literal [hi])", "hi"),
    ("((jopa syntax enable square_brackets) jopa string literal [hi]))","[hi]"),
    ("""(jopa syntax enable curly_braced_functions
         {x|jopa string create hello x} (jopa string create curly)
        )""", "hellocurly"),
    ("((jopa string surround (jopa string literal xs) (jopa string create y)))",
     "xsyxs"),
    ("(jopa example_prototype value)",                         "PROTOVALUE"),
    ("(jopa example_prototype whose (jopa example_prototype))","PROTOVALUE"),
    ("(jopa example_instance value)",                          "OVERRIDEN"),
    ("(jopa example_instance whose)",                          "OVERRIDEN"),
    ("(jopa example_prototype whose (jopa example_instance))", "OVERRIDEN"),
)

if __name__ == '__main__':
    for c, r in TESTS:
        try:
            e = JOPABrace(c).eval()
        except Exception, e:
            print 'WHILE EVALUATING "%s"' % c
            print traceback.format_exc(e)
        if not str(e) == r:
            print 'A test failed:            ', c
            print 'Evaluation returned:      ', e
            print 'Expected:                 ', r

