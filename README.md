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

JOPA
====

The project used to provide an interpreter in LEPL, but since then a new core
language was devised and named JOPA: Joys Of Partial Application.

It is smaller syntactically and it can be parsed without LEPL.
Heck, I even think about reimplementing it in C.

JOPA syntax rules:
1) Braces
2) Whitespace

A brace (f a b c) means:
	Take a function f
	call it with value a,
	call the result with the value b,
	call the result with the value c,
	stop and return
Empty braces () means None
(f) means f

Whitespace separates stuff inside braces

There is no special syntax for 'do not evaluate' like the Lisp's quote.

!) IMPORTANT A function does not get its parameter preevaluated.
What it gets is either an identifier (a string) or a brace (a code block)
The function predeclared whether it obtains a preevaluated brace or a literal

For examples of JOPA code refer to test_jopa.py

My JOPA interpreter offers REALLY EAGER EVALUATION
and tries to calculate something after each new succesfully obtained byte.
This is nicely demonstrated in a TRULY INTERACTIVE INTERPRETER demo.
Execute ./interactive_jopa.py to play with it

The transformations I want to see first:
{ abc }				<=>	(jopa function block (abc))
{ x | x }			<=>	(jopa function of x x)
'Hello!'			<=>	(jopa string literal (Hello!))
{ x | x }()			<=>	(jopa function of x x ())
{ x | x }('a')			<=>	(jopa function of x x ('a'))
xslang.context.set('a')(b)	<=>	(jopa context set a b)
a;b				<=>	(jopa operator last a b) ???
a.b				<=>	(a b) ???

