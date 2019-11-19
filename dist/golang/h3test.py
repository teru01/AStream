import urllib
from ctypes import *
import sys

pro = sys.argv[1]

if pro == "h3":
    lib = cdll.LoadLibrary("./h3client.so")
    client = lib.H3client
    url = "https://Mteru.local:6666/index.html"
elif pro == "h2":
    lib = cdll.LoadLibrary("./h2client.so")
    client = lib.H2client
    url = "https://Mteru.local:4443/index.html"
else:
    print("specify h2 or h3")
    exit(-1)

client.argtypes = [c_char_p]
client.restype = POINTER(c_ubyte*8)
# addr = GoString(url.encode('utf8'), len(url))
ptr = client(url.encode('utf8'))
length = int.from_bytes(ptr.contents, byteorder="little")
data = bytes(cast(ptr,
        POINTER(c_ubyte*(8 + length))
        ).contents[8:])
print(data)
