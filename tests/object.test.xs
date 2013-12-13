(xslang (# syntax) (# enable) (# rich)

.o .set (xslang.internals.empty ())

xslang.internals.inject o .val 3

xslang.internals.inject o .set_val {o v| xslang.internals.inject o .val v}

o.set_val o 4

o.val

)
###
X<int:4>
