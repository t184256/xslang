(xslang (# syntax) (# enable) (# rich)

.o .set (xslang.internals.empty ())

xslang.internals.inject o .val 3

xslang.internals.bind o .get_val {o| o.val}
xslang.internals.bind o .set_val {o v| xslang.internals.inject o .val v}
xslang.internals.inject o .set_val_ {o v| xslang.internals.inject o .val v}

o.set_val_ o 7
o.set_val 4

[
 o.get_val,
 o.val
]

)
###
X<X<int:4>,X<int:4>>
