(xslang (# syntax) (# enable) (# rich)
 .tpl .set (xslang.type.tuple)
 .t .set (tpl.empty.add .9 .add 3 .add (tpl.empty) .add 4)
 .t2 .set (tpl.empty.add (t.get 0) .add 3 .add (t.get 2) .add (t.length))
 xslang.operator.ternary (t.equals t2) t t2
)
###
X<tuple:X<'9'>,X<int:3>,X<tuple:>,X<int:4>>
