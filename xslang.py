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

# The differences:
# XSomething : XObject (dict-based, consumes strings and lookups them)
# XSomething : XClosure (a brace, a code block, a function, consumes anything)
# XClosure: has input parameters
# XClosure: collects input parameters one by one and stores them inside
# XClosure: parameters are named and can have default values
# function: an XClosure that started consuming parameters and will eval after
#       consuming all
# Binding arguments to a closure: {x y z| z y x} x_bound_value

# Everything is immutable!
# Everything (except funcs) is obtained by extending the XObject
# There should be a way to pass a parameter to a closure out-of-order
# xslang.function.pass_named_param func.__closure__ .paramname paramval

# character-based streams

### Definition of the basics ###

class XError(Exception):
    """ XSLang code execution error """

class XObject(dict):
    """ XSLang base type for dictionary-based objects """
    def __str__(self):
        if '__name__' in self:
            return 'X<%s>' % unbox(self['__name__'])
        if '__string__' in self: return unbox(self['__string__'])
        # TEMP hack
        if '__py_val__' in self and '__py_type__' in self:
            if self['__py_type__'] == 'none': return 'X<none>'
            if self['__py_type__'] == 'string':
                return "X<'%s'>" % self['__py_val__']
            return 'X<(%s:%s)>' % (self['__py_type__'], self['__py_val__'])
        return 'X<:%s:>' % ' '.join(self.keys())
    def __call__(self, arg, context=None): # functions override this
        #print 'LOOKUP', self, arg
        #if '__py_val__' in self:
            #print 'LOOKUP in primitive!:', unbox(self), unbox(arg)
        if not '__py_type__' in arg or arg['__py_type__'] != 'string':
            raise XError('The key is not a string "%s" <- "%s"' % (self, arg))
        return self[unbox(arg)]
    def extend(self, name, arg):
        new_dic = self.copy()
        new_dic[name] = arg
        new = self.__class__(new_dic)
        if any(not k in new for k in self.keys()): raise XError('Bad extension')
        return new
    def ext(self, *a, **kwa):
        new_dic = self.copy()
        for dic in a: new_dic.update(dic)
        new_dic.update(kwa)
        new = self.__class__(new_dic)
        if any(not k in new for k in self.keys()): raise XError('Bad extension')
        return new
    def __setattr__(self, n, v):
        raise XError('Setting attribute %s.%s is a bad idea' % (type(self), n))

Xobject = XObject()

_gen_type = lambda type_name, def_val: Xobject.ext({
        'base':  Xobject.ext(__py_type__=type_name, __py_val__=def_val)
})

xslang = Xobject.ext({
    'type': Xobject.ext({
        'bool': Xobject.ext({
            'base':     Xobject.ext(__py_type__='bool'),
            'true':     Xobject.ext(__py_type__='bool', __py_val__=True),
            'false':    Xobject.ext(__py_type__='bool', __py_val__=True),
         }),
        'int':      _gen_type('int', 0),
        'none':     _gen_type('none', None),
        'string':   _gen_type('string', ''),
        'list':     _gen_type('list', list())
    })
})

### Primitive type (which maps to a simple python type) ###

def box(pyval):
    # Needs to actually extend existing prototypes (with methods)
    # not XObject
    if isinstance(pyval, bool):     base = 'bool'
    elif isinstance(pyval, int):    base = 'int'
    elif pyval is None:             base = 'none'
    elif isinstance(pyval, str):    base = 'string'
    elif isinstance(pyval, tuple):  base = 'list'
    elif hasattr(pyval, '__iter__'):base = 'list'; pyval = list(pyval)
    else: raise XError('How to box type %s?' % type(pyval))
    base = xslang['type'][base]['base']
    return base.extend('__py_val__', pyval)

def unbox(Xval):
    if not '__py_type__' in Xval or not '__py_val__' in Xval:
        raise XError('How to unbox %s?' % Xval)
    return Xval['__py_val__']

### Nice names for packages ###

xslang = xslang.extend('__name__', box('xslang root package'))
xslang = xslang.extend('type',
        xslang['type'].extend('__name__', box('xslang.type package'))
)

### Streaming ###

def stream_str(string):
    while True:
        if not string: return
        c, string = string[0], string[1:]
        yield c

def stream_read_single(stream):
    """
    Converts '(xslang operator) ident') to a stream of
    ('(', 'xslang', ' ', 'operator', ')', ' ', 'ident')
    """
    s = ''
    for c in stream:
        s += c
        if s:
            if s[-1] == '(' or s[-1].isspace():
                if s[:-1]: yield s[:-1]
                yield s[-1]; s = ''
        if s:
            if s[-1] == ')': yield s[:-1]; yield s[-1]; s = ''
    if s: yield s

def stream_read_piece(stream):
    """
    Converts '(xslang operator) ident') to a stream of
    ('(', 'xslang', 'operator', ')', 'ident')
    """
    for t in stream_read_single(stream):
        if not t.isspace(): yield t

def stream_read_until_closing_brace(stream, opened=1):
    s, b = '', opened
    for c in stream:
        s += c
        if c == '(': b += 1
        elif c == ')':
            b -= 1
            if not b: return s
        if not b and s and not s.isspace() and c.isspace(): return s[:-1]
    if b: raise XError('Unbalanced braces: "%s"' % s)
    return s

flatten = lambda s, *a: ''.join(list(
    stream_read_until_closing_brace(stream_str(s), *a)))
assert flatten('abc', 0) == 'abc'
assert flatten('()', 0) == '()'
assert flatten('(abc) xef)', 0) == '(abc)'
assert flatten('(abc) xef)', 1) == '(abc) xef)'
assert flatten(' (abc) (def)', 0) == ' (abc)'

### Arguments collector: the closure, the context ###

class XContext(XObject):
    """
    A closure, a context, an arg collector.
    It wraps an evalable (a XPyFunc or an XInterpreter).
    Is immutable.

    It collects all necessary argument values
    and evaluates on consuming the last one.

    It can collect args with different lookup policies:
        1) require a parameter to be provided with __call__
        2) lookup parameter in current context
        3) have a default (bound) value of a parameter
    One day { in1 in2 ^outer bound_x=x | ... } will mean that
        1) bound_x gets bound at the moment of context definition
            self.args_bound['bound_x'] = x  (like inherited from parent context)
        2) outer will be looked up in another parent context
            upon evaluating the body
        3-4) in1 and in2 will be consumed with __call__
    After that the function will evaluate,
    to prevent it require one more argument and pass it later.
    """

    def __init__(self, wrapped, argnames=None, argvals=None, stream=False):
        if wrapped.__class__ == dict:
            XObject.__init__(self, wrapped)
        else:
            if isinstance(wrapped, str) or stream:
                #print 'WRAPPING', wrapped
                wrapped = XInterpreter(wrapped)
            self['wrapped'] = wrapped
            self['__py_arg_names__'] = argnames if argnames else []
            self['__py_arg_vals__'] = argvals if argvals else {}
            self['xslang'] = xslang
            self['__name__'] = box('XContext "%s"' % self['wrapped'])
        # Let's evaluate and cache this
        self['valless'] = list(a for a in self['__py_arg_names__']
                               if not a in self['__py_arg_vals__'])
        #print 'XContextNEW', n, self['valless']
        #print 'XContextNEW', type(self['wrapped']), self['valless'], self.keys()
        #print 'XContextNEW', self['__py_arg_names__'], self['__py_arg_vals__']
        if self['wrapped'].__class__ == dict: raise XError('PANIC!')

    @staticmethod
    def create(*a, **kwa):
        n = XContext(*a, **kwa)
        return n.try_eval()

    def with_addn_arg(self, argn, def_val=None):
        new_argvals = self.argvals.copy()
        if not def_val is None: new_argvals[argn] = def_val
        return self.ext({
            '__py_arg_names__': self.argnames + (argn,),
            '__py_arg_vals__': new_argvals,
        })

    def with_addn_val(self, val, argn=None, context=None):
        if argn is None: argn = self['valless'][0]
        new_argvals = self['__py_arg_vals__'].copy()
        new_argvals[argn] = val
        new_self = self.ext({
            '__py_arg_names__': self['__py_arg_names__'],
            '__py_arg_vals__': new_argvals,
        })
        #print 'NEW valless', new_self['valless']
        return new_self.try_eval()

    def __call__(self, v, context=None):
        #print 'valless', self['wrapped'], self['valless'], '<-', v
        if not self['valless']:
            raise XError('already not valless! (%s <- %s)' % (self, v))
        #print 'collected val', self, v
        return self.with_addn_val(v, context=None)

    def try_eval(self):
        if not self['valless']:
            return self['wrapped'].eval(
                context=self.ext(self['__py_arg_vals__']))
        return self


#    def parent_lookup(self, argname, context):
#        if context and argname in self.args_lookup:
#                if argname in context: return True
#        return False


### The main thing: the interpreter ###

def box_unknown(val):
    #print 'BOX UNKNOWN "%s"' % val
    return box(val)

class XInterpreter(XObject):
    """
    Is not immutable, has state. Thus it is dirty and non-reusable.
    Wraps "f arg1 (...) arg2 arg3" xslang code into an evalable.

    It parses and executes the xslang code stream.

    Unknown tokens will be treated in a custom configurable manner:
        a custom function will decide whether to wrap into string, error out,
        do a recursive parent context lookup or whatever else.
    """

    def __init__(self, src=None): #, parent=None, auto_eval=True):
        if src.__class__ == dict:
            #print 'EXTENSION OF XInterpreter'
            XObject.__init__(self, src); return
#       self.auto_eval = auto_eval
        self['stream'] = stream_str(src) if isinstance(src, str) else src
        self['convert_unknown_tokens'] = box_unknown
        # here could be autolookup, raise Exception or whatever else
        self['state'] = None
        self['__name__'] = box('interpreter')

    def __call__(self, t, context=None):
        if self['state'] is None: self['state'] = t
        else: self['state'] = self['state'](t, context=self)
        if '__hack_apply__' in self['state']:
            #print 'got hack', self['state']['__hack_apply__']
            self['state'] = self['state']['__hack_apply__'](self)
            #print 'hack resulted in', hack_result
            #if hack_result is not None: self['state'] = hack_result

    def process_token(self, t, context):
        if not context: raise XError("NCTX")
        if t == '(':
            return XContext.create(
                    stream_read_until_closing_brace(self['stream']))
#        elif t in self: return self[t]
        elif context and t in context: return context[t]
        return self['convert_unknown_tokens'](t)

    def eval(self, context=None):
        """ Evaluate the body after collecting the parameters """
        self['ctx'] = context # to be able to to change it with hacks
        for t in stream_read_piece(self['stream']):
            if t == ')':
                #raise XError('CLOSING BRACE')
                break
            else: t = self.process_token(t, context)
            self(t, context=context)

        return self['state']

### Utilities for wrapping Python functions with XContexts ###

class XPyFuncContainer_(XObject):
    def eval(self, context=None):
        inject = []
        if context:
            for argname in context['__py_arg_names__']:
                inject.append(context['__py_arg_vals__'][argname])
        return self['__py_func__'](*inject, context=context)
XPyFuncContainer = XPyFuncContainer_()

def XPyFunc(pyfunc, argnames=None, argvals=None):
    c = XPyFuncContainer.ext(__py_func__=pyfunc, __name__=box(pyfunc.func_name))
    return XContext(c, argnames=argnames, argvals=argvals)

def XWrappedPyFunc(*argnames, **argvals):
    def wrapper(func):
        return XPyFunc(func, argnames, argvals).ext(name=func.func_name)
    return wrapper

### Hacks ###

def XHackApply(xobj): return Xobject.ext(__hack_apply__=xobj)

@XWrappedPyFunc('hack')
def hack_apply(xobj, context=None): return XHackApply(xobj)

@XWrappedPyFunc('xinterp')
def hack_literal(xinterp, context=None):
    """ xslang hack apply (xslang hack literal) ( l) -> ' l' """
    literal = stream_read_until_closing_brace(xinterp['stream'], 0)
    literal = literal.strip()
    if literal.startswith('(') and literal.endswith(')'):
        literal = literal[1:-1]
    return box(literal)

hack = Xobject.ext({'__name__': box('xslang.hack package'),
    'apply': hack_apply,
    'literal': hack_literal,
})

xslang = xslang.ext(hack=hack)

### Python-implemented functions ###

def Xdummy_py(context=None):
    return box('dummy')
Xdummy = XPyFunc(Xdummy_py).ext(__name__=box('dummy func'))

def Xprint_py(arg, context=None):
    print 'Printing in', context, type(context),
    print '           ', context.keys()
    print 'arg present:', 'arg' in context
    print 'arg:', arg
    #print 'lookup:', context[context['arg']]
Xprint = XPyFunc(Xprint_py, argnames=('arg',)).ext(__name__=box('print func'))

def Xreverse_concat_py(str1, str2, context=None):
    return box(unbox(str2) + unbox(str1))
Xreverse_concat = XPyFunc(Xreverse_concat_py, argnames=('str1', 'str2')).ext(
        __name__=box('print func'))

xslang = xslang.ext({
    'dummy': Xdummy,
    'print': Xprint,
    'reverse_concat': Xreverse_concat,
})

# Ideas for requesting args:
# f = (xslang function of (a b c=d) (c b a))

#print Xprint
#print XContext.create('xslang (print)')
#print XContext.create('xslang literal xslang')
#print XContext.create('xslang reverse_concat (WORLD!) HELLO')
#print XContext.create(
#    'xslang reverse_concat (xslang reverse_concat RLD! WO) HELLO')
#print XClosure('xslang print xslang').eval()
#print XClosure('xslang print (xslang (type) str base)').eval()

# interactive evaluation:
# * xslang syntax enable rich (
# ** something is going on here
# !! Something arg1='is', arg2='going' arg3='here'
# *)
#
# > xslang syntax enable rich (something is going on here

if __name__ == '__main__': print XContext.create(raw_input())
