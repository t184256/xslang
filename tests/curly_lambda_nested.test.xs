DISABLED
(xslang (# syntax) (# enable) (# curly_braced_functions)
 xslang (# syntax) (# enable) (# dotty_literals)
 xslang.context.set.ctx xslang.context
 { p |
  ctx.set.somename { unused | {x} }
  ctx.set.rev { y x | x y }
  rev .context xslang p (somename ()) .HELLO
  ctx.get (somename())
 } .set
)
###
X<'HELLO'>
