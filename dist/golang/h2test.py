import urllib
from ctypes import *
import sys
import threading
import time

lib = cdll.LoadLibrary("./h2client.so")
client = lib.H2client
url = "https://dash.localdomain:4443/fall.jpg"

client.argtypes = [c_char_p]
client.restype = POINTER(c_ubyte*8)
# addr = GoString(url.encode('utf8'), len(url))

def download():
    ptr = client(url.encode('utf8'))
    length = int.from_bytes(ptr.contents, byteorder="little")
    data = bytes(cast(ptr,
            POINTER(c_ubyte*(8 + length))
            ).contents[8:])

def main():
    start = time.time()
    threads = []
    for i in range(3):
        t = threading.Thread(target=download)
        threads.append(t)
        t.start()
        # print(data)
    for t in threads:
        t.join()
    print(time.time() - start)

if __name__ == "__main__":
    main()
