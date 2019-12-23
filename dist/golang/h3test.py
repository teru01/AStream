import urllib
from ctypes import *
import sys
import threading
import time

lib = cdll.LoadLibrary("./h3client.so")
client = lib.H3client
url = "https://dash.localdomain:6666/BBB-I-720p.seg0-L0.svc"

client.argtypes = [c_char_p, c_int]
client.restype = POINTER(c_ubyte*8)
# addr = GoString(url.encode('utf8'), len(url))
def download(unreliable):
    if unreliable:
        flag = 1
    else:
        flag = 0
    ptr = client(url.encode('utf8'), flag)
    length = int.from_bytes(ptr.contents[:8], byteorder="little")
    validOffset = int.from_bytes(ptr.contents[8:16], byteorder="little")
    data = bytes(cast(ptr,
            POINTER(c_ubyte*(8 + length))
            ).contents[8:])
    return data, validOffset

def main():
    payload, o = download(True)
    print(len(payload), o)
    payload, o = download(False)
    print(len(payload), o)

    # start = time.time()
    # threads = []
    # for i in range(50):
    #     t = threading.Thread(target=download)
    #     threads.append(t)
    #     t.start()
    #     # print(data)
    # for t in threads:
    #     t.join()
    # print(time.time() - start)

if __name__ == "__main__":
    main()
