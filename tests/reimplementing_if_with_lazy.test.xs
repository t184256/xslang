(xslang (# syntax) (# enable) (# rich)

.if .set {cond if_body else_body |
 xslang.operator.ternary (cond)
  (xslang.operator.lazy 2 (if_body))
  (xslang.operator.lazy 2 (else_body))
}

if (xslang.type.bool.true) { 'HELLO' } { xslang.operator.abort 'DEAD' }

)
###
X<'HELLO'>
