import urllib
from ctypes import *
import sys


lib = cdll.LoadLibrary("./h2client.so")
client = lib.H2client
url = "https://dash.localdomain:4443/index.html"

client.argtypes = [c_char_p]
client.restype = POINTER(c_ubyte*8)
# addr = GoString(url.encode('utf8'), len(url))

for i in range(2):
    ptr = client(url.encode('utf8'))
    length = int.from_bytes(ptr.contents, byteorder="little")
    data = bytes(cast(ptr,
            POINTER(c_ubyte*(8 + length))
            ).contents[8:])
    print(data)
