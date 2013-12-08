(xslang (# syntax) (# enable) (# rich)
 .recloop .set { acc i |
  xslang.operator.if (i.equals(8))
  { acc .concatenate (i.string) }
  { recloop (acc .concatenate (i.string)) (i.add 2) }
 }
 recloop .() 0
)
###
X<'02468'>
