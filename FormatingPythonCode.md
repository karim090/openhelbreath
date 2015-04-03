There is some rules that are restricted.

# **Tabulations instead of spaces** #
```
def asdf(self, zxcv):
->print "zxcv"
#-> means \t (tab)
```

# **PRINT and other keywords** #
Don't use spaces as explained below:
```
print "123456789"
```
# **PRINTING text** #
Don't use
```
print "asdf", var1, "zxcv"
```
Whenever possible use
```
print "asdf %d zxcv" % (var1)
```
# **Classes** #
C in front of class name IE:
```
class CClassName(object):
->pass
#-> means \t (tab)
```
# **Hungarian notation** #
m\_iVar1 etc. See http://en.wikipedia.org/wiki/Hungarian_notation for further informations.


**Just simply look at the code and try to format it as others**