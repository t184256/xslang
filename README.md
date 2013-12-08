xslang
======

an eXtensible Syntal LANGuage experiment

This is an toy experiment aimed at creating a programming language
with the possibility of changing the syntax during interpretation.

This means implementing a core language and an interpreter,
that would allow applying additional source-to-source transformations during interpretation.

Thus the source will undergo several source-to-source transformations
before getting translated into the core language subset and guess what?
The programmer would be free to specify which transformations apply to which parts of the code!
So, for example, whitespace-matters-haters could use libraries written by curly-braces-haters
without forcing a single syntax on everyone.

That's how I see it at some point in the future:

```
xslang.syntax.enable('hash-comments');
# Pheww. I was tired of those slashy comments.
# I think I also want a nicer ternary operator
{
  xslang.syntax.enable('python-style-inline-if-else')
  xslang.syntax.enable('braceless-calls')
  a = b if check b else c
  # I miss C ternary operator. I want both.
  xslang.syntax.enable('c-style-ternary-operator')
  # Oh, and the return
  xslang.syntax.enable('return')
  return { x | x.str ? x.str : 'not specified' }
}
```

The phases of the project:

1) Devising the core language (WIP)

2) Implementing an interpreter for it (WIP)

3) Writing a standard library for it

4) Choosing how the source-to-source transformations should be defined
(regexps? LEPL-assisted transformations? lower priority identifier redefinitions? custom executable rewriters?)
and stacked.

5) Implementing those transformations

???) ...

PROFIT) Creating a language that could be used with any syntax imaginable!

XSLang
======

The project used to provide an interpreter in LEPL,
then a core language named JOPA (Joys Of Partial Application,
but now a core language named XSLang is used.

It is pretty small syntactically and is interpreted with pure python.
So pure that no imports are used.
Heck, I even think about reimplementing it in C.

XSLang (in its core variation) has two syntax rules, braces and whitespace

A brace (f a b c) means:

	Lookup f in current context, mutate it if needed,

	lookup a in current context, mutate it if needed

	call f with a, mutate the result if needed

	call the result with b, mutate if needed

	call the new result with c, mutate if needed

	stop and return the newest result

Mutation is a funny concept.
It works like this: any temporary or final result of the evaluation is free
to mutate into some other object or abort the mutation.
During the mutation it's free to do anything nasty to the interpreter.
Look at this as an extension point for the interpreter, so that it fits into
less than hundred lines of code.
Things implemented with mutation are literal creation and lazy evalutaion of
bound methods
(int.string creates a string on instantiation, but string.length doesn't create
an int so there isn't a loop).
Things to be implemented with mutation are infixator (a converter of a prefix
operator into an infix operator) and whatever else would seem nice to me.

By default, two objects are available in the namespace.
'xslang' gives access to the standard library and '#' mutates the next argument
into a string literal.

'Do not evaluate' like the Lisp's quote is also done with #.

For examples of XSLang code refer to the tests folder.

My XSLang interpreter offers REALLY EAGER EVALUATION
and tries to calculate something after each new succesfully obtained byte.
This is nicely demonstrated in a TRULY INTERACTIVE INTERPRETER demo.
Execute './interactive.py +rich' to play with it.

The key point of XSLang is its possibility to enable syntax transformations for
some parts of the code in runtime.

Transformations do something like this:

```
{ abc }				<=>	(xslang.function.block.(abc))
{ x | x }			<=>	(xslang.function.of.x.x)
'Hello!'			<=>	(xslang.string.literal (# Hello!))
{ x | x }()			<=>	(xslang.function.of x x ())
{ x | x }('a')			<=>	(xslang.function.of x x ('a'))
xslang.context.set('a')(b)	<=>	(xslang.context.set.a b)
a;b				<=>	(xslang.operator.last.a b) ???
a.b				<=>	(a b) ???
```

One day I would document XSLang more thoroughly, but for now refer to the
source (there is not much!) and to the tests. Sorry for the inconvenience.
