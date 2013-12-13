(xslang (# syntax) (# enable) (# rich)

 xslang.internals.extend (xslang.type.int) .greater_than
  (xslang.internals.pyfunc .(Xbool int.greater_than(a:int b:int) a > b))

 [1, 2, 3, 5, 6, 9, 4, 2, 1] .map (xslang.type.int.greater_than 4)

)
###
X<X<true>,X<true>,X<true>,X<false>,X<false>,X<false>,X<false>,X<true>,X<true>>
