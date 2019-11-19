import urllib
from ctypes import *

class GoString(Structure):
    _fields_ = [("p", c_char_p), ("n", c_longlong)]

lib = cdll.LoadLibrary("./h3client.so")

lib.Add.argtypes = [c_longlong, c_longlong]
print ("awesome.Add(12,99) = %d" % lib.Add(12,99))

lib.Request.argtypes = [GoString]
url = "https://Mteru.local:6666/index.html"
addr = GoString(url.encode('utf8'), len(url))
lib.Request(addr)
