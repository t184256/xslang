DISABLED
(xslang (# syntax) (# enable) (# rich)
 xslang.type.string.constants.newline.join(
  ( 10 .to 0 ).map { i |
   xslang.operator.if (i.equals 1)
    {i.string.concatenate ' bottle of beer'}
    {i.string.concatenate ' bottles of beer'}
  }
 )
 .concatenate xslang.type.string.constants.newline
 .concatenate 'No more bottles of beer'
)
###
X<'10 bottles of beer
9 bottles of beer
8 bottles of beer
7 bottles of beer
6 bottles of beer
5 bottles of beer
4 bottles of beer
3 bottles of beer
2 bottles of beer
1 bottle of beer
No more bottles of beer'>
