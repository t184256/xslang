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
(character stream transformations? regexps? LEPL-assisted transformations?
lower priority identifier redefinitions? custom executable rewriters?)
and stacked.

5) Implementing those transformations

???) ...

PROFIT) Creating a language that could be used with any syntax imaginable!

XSLang
======

The project used to provide an interpreter in LEPL,
then a core language named JOPA (Joys Of Partial Application,
but now a core language named XSLang is used.

It is pretty small syntactically and is interpreted with pure Python.
So pure that no imports are used.
Heck, I even think about reimplementing it in Vala or C.

XSLang (in its core variation) has two syntax rules, braces and whitespace

A brace (f a b c) means:

	Lookup f in current context

	lookup a in current context

	call f with a

	call the result with b

	call the new result with c

	stop and return the newest result

For examples of XSLang code refer to the tests folder.

The key point of XSLang is its possibility to enable syntax transformations for
some parts of the code in runtime.

Context pollution is taken seriously: apart from the 'xslang' variable
any new context must explicitely define what it borrows from the definition
context and what it takes from the evaluation context.
Poisoning parent contexts is forbidden too, but that's not so unusual.

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

One day I would document XSLang more thoroughly, (and stop rewriting it!)
but for now refer to the source (it's not so long!) and to the tests.
Sorry for the inconvenience.
