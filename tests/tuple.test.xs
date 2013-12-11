(xslang (# syntax) (# enable) (# rich)
 .tpl .set xslang.type.tuple
 .t .set (tpl.empty
  .add .9
  .add 3
  .add (tpl.empty.add 4 .add (tpl.empty.add tpl.empty) .add tpl.empty)
  .add 4
 )
 .t2 .set [(t.get 0),3, [4, [[]], [  ]] , t.length]
 xslang.operator.ternary (t.equals t2) t t2
)
###
X<X<'9'>,X<int:3>,X<X<int:4>,X<X<>>,X<>>,X<int:4>>
