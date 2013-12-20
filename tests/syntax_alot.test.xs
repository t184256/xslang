xslang hack apply (xslang hack syntax) curly_functions
xslang hack apply (xslang hack syntax) left_assignment
xslang hack apply (xslang hack syntax) tilda_apply

:= a HELLO
:= b WORLD!

:= concat { x y | xslang reverse_concat y x }

concat a b
###
X<'HELLOWORLD!'>
:= set (:=)
