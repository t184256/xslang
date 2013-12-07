DISABLED
(xslang (# syntax) (# enable) (# rich)
 .recloop .set { i acc |
  xslang.operator.if (i.equals(8))
  { acc .concatenate (i.string) }
  { recloop (i .add 2) (acc .concatenate (i.string)) }
 }
 recloop 0 (#())
)
###
X<'02468'>
