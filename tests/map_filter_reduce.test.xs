(xslang (# syntax) (# enable) (# rich)
 .t .set [1, 2, 3, 4, 5]
 .f .set {x| x.equals 3 }
 .sum .set {x| (x.reduce {acc x| acc.add x})}
 [
  t.filter f,
 sum(t.map {x| x.add 1})
 ]
)
###
X<X<X<int:3>>,X<int:20>>
