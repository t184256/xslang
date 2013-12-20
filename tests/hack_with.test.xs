xslang hack apply (xslang hack syntax) curly

xslang hack apply {xslang hack with} a HELLO

xslang hack apply (xslang hack with) b WORLD!

xslang hack apply (xslang hack with) concat
(
 xslang hack apply (xslang hack block) (x y)
 (xslang reverse_concat y x) try_eval
)

concat a b
###
X<'HELLOWORLD!'>
