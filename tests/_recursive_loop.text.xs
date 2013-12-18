DISABLED
(xslang (# syntax) (# enable) (# rich)
 .n .set 9
 xslang.context.set .recloop { i acc |
  xslang.operator.if (i.equals 0)
  { acc }
  { recloop (i .subtract 1) (acc .concatenate 'O') }
 }
 (recloop n 'L') .concatenate 'NG'
)
###
X<'LOOOOOOOOONG'>
