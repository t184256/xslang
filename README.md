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

That's how I see it:

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

Currently the project provides an interpreter of a tiny toy language.
The interpreter is written in Python and uses a nice library named LEPL.

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

I totally understand the language will never get popular;
I actually plan to obtain fun from devising transformations like this and seeing them working:

```
a = b <=> xslang.context.update('a', b)
[a, b, c] = {l = xslang.stdlib.list(); l.add(a); l.add(b); l.add(c); l}
```
