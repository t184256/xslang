(xslang (# syntax) (# enable) (# dotty_literals)
 xslang.context.set .hi .HELLO
 xslang.context.set .func_reverse (
  xslang.function.of .func (# ((
   xslang.function.of .first (# ((
    xslang.function.of .last (# ((
     func last first
    )))
   )))
  )))
 )
 func_reverse xslang .get .context .hi
)
###
X<'HELLO'>
