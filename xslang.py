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

import types
from lepl import *

### Language constructs ###

class XSLangObject(object):
    def __init__(self, string=None, call=None):
        self.dic = {}
        if string is not None: self._contained_string = string
        if call is not None:
            # requires a function that accepts:
            #    self : XSLangObject, x : Context, param : XSLangObject
            self._called_paramname = 'pyfuncarg'
            self.call = types.MethodType(
                    (lambda s, x: call(s, x,
                            x.get_o('pyfuncarg', maxdepth=0, pop=True))),
                    self, XSLangObject
            )

    @staticmethod
    def function(pyfunc): return XSLangObject(call=pyfunc)

    def __str__(self):
        if '_contained_string' in self.__dict__:
            return "XSLangObject: '"+self._contained_string+"' " + str(self.dic)
        return object.__str__(self) + ' ' + str(self.dic)

    def __setitem__(self, name, obj): self.dic[name] = obj
    def __getitem__(self, name): return self.dic[name]

def _tryget(cstack, name, maxdepth=-1, pop=False):
    if not cstack: return None
    if name in cstack[-1]:
            r = cstack[-1][name]
            if pop: del cstack[-1][name]
            return r
    return _tryget(cstack[:-1], name, maxdepth - 1, pop) if maxdepth != 0 else None

class XSLangBase(object):
    def __init__(self, root_object):
        self.contextstack = [
            {'xslang': root_object}
        ]

    def set_o(self, name, obj):
        self.contextstack[-1][name] = obj

    def get_o(self, name, maxdepth=-1, pop=False):
        return _tryget(self.contextstack, name, maxdepth-1, pop)

    def new_context(self):
        self.contextstack.append(dict())

    def drop_context(self):
        del self.contextstack[-1]


### Syntax constructs that form the syntax tree ###

class XSLangExpression(List):
    def evl(self, x):
        return [e.evl(x) for e in self][-1]

class XSLangParam(List): pass
class XSLangFunction(List):
    def evl(self, x):
        newfunc = XSLangObject()
        newfunc._called_expr = self[1]
        newfunc._called_paramname = self[0][0]
        newfunc.call = types.MethodType(
                (lambda self, x: self._called_expr.evl(x)),
                newfunc, XSLangObject
        )
        return newfunc

class XSLangDot(List):
    def evl(self, x):
        left = self[0].evl(x)
        right = self[1][0]
        return left.dic[right]
#def XSLangDotCreate(l): return XSLangDot(l[0])

XSLangFunctionWoXSLangParam = lambda l: XSLangFunction([XSLangParam([''])] + l)
class XSLangCall(List):
    def evl(self, x):
        func = self[0].evl(x)
        x.new_context()
        if len(self) == 2:
            paramval = self[1]
            x.set_o(func._called_paramname, paramval.evl(x))
        val = func.call(x)
        x.drop_context()
        return val
#def XSLangCallCreate(l): return XSLangCall(l[0])

class XSLangIdentifier(List):
    def evl(self, x):
        return x.get_o(self[0])
class XSLangString(List):
    def evl(self, x):
        return XSLangObject(string=self[0])


### Syntax definition ###

L = lambda c: Drop(Literal(c))

WHITESPACE = Optional(L(' ') | L('\t') | L('\n'))
FORBIDDEN = ';{}|().\''
WORD = AnyBut(FORBIDDEN)[1:,...]

with DroppedSpace():
    EXPR = Delayed()
    EXPRATOM = Delayed()
    IDENTIFIER = WORD > XSLangIdentifier
    STRING = WHITESPACE & SingleLineString(quote='\'') & WHITESPACE > XSLangString
    BRACED = L('(') & EXPR & L(')') > XSLangExpression
    G1 = BRACED | STRING | IDENTIFIER
    DOT = EXPRATOM & L('.') & IDENTIFIER > XSLangDot
    G2 = DOT | G1
    CALL = (
            (EXPRATOM & L('(') & EXPR & L(')')) | \
            (EXPRATOM & L('(') & L(')')) \
            ) > XSLangCall
    G3 = CALL | G2
    FUNCNP = (L('{') & EXPR & L('}')) > XSLangFunctionWoXSLangParam
    PARAM = WORD > XSLangParam
    FUNCWP = (L('{') & PARAM & L('|') & EXPR & L('}')) > XSLangFunction
    FUNC = FUNCNP | FUNCWP
    G4 = FUNC | G3
    EXPRATOM += G4 > XSLangExpression
    EXPR += EXPRATOM[1:, L(';')] > XSLangExpression
    EXPREOS = EXPR & ~Eos()
    EXPREOS.config.auto_memoize()

### Standard library definition (the xslang.***) ###

greet = XSLangObject(call=(lambda s, f, a: 'Greetings!'))

@XSLangObject.function
def greet_smb(self, x, param):
    if param is None: return XSLangObject(string='Greetings, stranger!')
    return XSLangObject(string='Greetings, ' + param._contained_string + '!')

class XSLangPackage(XSLangObject):
    def __init__(self, inject_dic=None):
        XSLangObject.__init__(self)
        self.dic.update(inject_dic or {})

@XSLangObject.function
def xslang_print(self, x, param):
    import sys
    sys.stdout.write(param._contained_string or '???')
    return param

@XSLangObject.function
def xslang_println(self, x, param):
    import sys
    sys.stdout.write(param._contained_string or '???')
    sys.stdout.write('\n')
    return param

@XSLangObject.function
def xslang_concat(self, x, param):
	p = param._contained_string if param else ''
	return Concatenator(p)
def xslang_concat_combine(self, x, param):
    return Concatenator(self.dic['string']._contained_string
		    + param._contained_string)
class Concatenator(XSLangObject):
    def __init__(self, string):
        XSLangObject.__init__(self, string=string, call=xslang_concat_combine)
        self.dic['string'] = XSLangObject(string=string)

class XSLangRootObject(XSLangObject):
    def __init__(self):
        self.dic = {
            'fun': XSLangObject(call=(lambda s, x, p: p)),
            'greetings': XSLangPackage({
                'hw': XSLangObject(string='Hello World!'),
                'greet': greet,
                'greet_smb': greet_smb,
            }),
            'operator': XSLangPackage(),
            'string': XSLangPackage({
                'concat': xslang_concat,
                'reverse': XSLangObject(call=(lambda s, x, p: (
                        XSLangObject(string=(p._contained_string[::-1]))))),
                'print': xslang_print,
                'println': xslang_println,
            }),
        }
        identity = XSLangEval('{x|x}', rootobj=self)
        self.dic['operator']['identity'] = identity

### The interpreter ###

def XSLangEval(code, printtree=False, rootobj=None):
    x = XSLangBase(rootobj or XSLangRootObject())
    try:
        for e in EXPREOS.get_parse_string()(code):
            if printtree: print e
            r = e.evl(x)
            return r
    except Exception as e:
        print e


### The tests ###

TESTS = {
    "'a'"                                           : 'a',
    "{{x|x}('a')}()"                                : 'a',
    "{{'a'}}()()"                                   : 'a',
    "xslang.greetings.hw"                           : 'Hello World!',
    "{xslang.greetings.hw}()"                       : 'Hello World!',
    "{xslang.greetings.hw}('a')"                    : 'Hello World!',
    "{x|xslang.greetings.greet_smb(x)}()"           : 'Greetings, stranger!',
    "{x|xslang.greetings.greet_smb(x)}('Dan')"      : 'Greetings, Dan!',
    "xslang.string.print('a')"                      : 'a',
    "xslang.string.println('a')"                    : 'a',
    "(xslang.string.concat()('a')).string"          : 'a',
    "(xslang.string.concat('a')('b')('c')).string"  : 'abc',
    "xslang.string.reverse('130')"                  : '031',
    "xslang.operator.identity('a')"                 : 'a',
}

def tests(printtree=False):
    for c, s in TESTS.items():
        v = XSLangEval(c, printtree)
        if v is not None:
            if not isinstance(v, str):
                if '_contained_string' in v.__dict__:
                    v = v._contained_string
                else:
                    v = 'NO STRING'
            else:
                v = 'PYTHON STRING [' + v + ']'
        else:
            v = 'NONE RETURNED'
        print 'Test:', 'success' if v == s else 'FAILURE!', c, s, v

### The REPL ###

def main():
    import sys
    if sys.argv[1:] == ['tests']: return tests()
    while True:
        try:
            code = raw_input('xslang-core> ')
            print XSLangEval(code, printtree=True)
        except EOFError as e:
            print
            return

if __name__ == '__main__': main()

