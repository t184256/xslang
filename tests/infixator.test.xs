DISABLED
(xslang (# syntax) (# enable) (# rich)

.- .set (xslang.operator.lazy 2 {~ xslang.type.int.subtract})

.+ .set .add

[3 + 2, 7 - 3, xslang.type.tuple.empty + 'a' + 'b' + 'c']]

)
###
X<X<int:5>,X<int:4>,X<X<'a'>,X<'b'>,X<'c'>>>

