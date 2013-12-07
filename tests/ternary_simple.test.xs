(xslang (# syntax) (# enable) (# rich)
 xslang.operator.ternary (xslang.type.bool.false)
  .TRUE1
  (xslang.operator.ternary (xslang.type.bool.true)
   .TRUE2
   .FALSE
  )
)
###
X<'TRUE2'>
