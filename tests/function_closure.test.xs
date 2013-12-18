DISABLED
(xslang (# syntax) (# enable) (# rich)

.o .set 3

.meth .set (
 .func_broken .set {a b| a .subtract b}
 .func .set (xslang.function.dualarg .a .b (# (a .subtract b)))
 func o
)

meth 4

)
###
X<int:-1>
