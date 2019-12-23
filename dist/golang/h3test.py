import urllib
from ctypes import *
import sys
import threading
import time

lib = cdll.LoadLibrary("./h3client.so")
client = lib.H3client
url = "https://dash.localdomain:6666/BBB-I-720p.seg0-L1.svc"

client.argtypes = [c_char_p, c_int]
client.restype = POINTER(c_ubyte*16)
# addr = GoString(url.encode('utf8'), len(url))
def download(unreliable):
    if unreliable:
        flag = 1
    else:
        flag = 0
    ptr = client(url.encode('utf8'), flag)
    length = int.from_bytes(ptr.contents[:8], byteorder="little")
    validOffset = int.from_bytes(ptr.contents[8:16], byteorder="little")
    # print("ptr.contents[8:9]: ", ptr.contents[8:9])
    data = bytes(cast(ptr, POINTER(c_ubyte*(16 + length))).contents[9:])
    return length, data, validOffset

def main():
    l, payload, o = download(True)
    print(l, len(payload), o)
    l, payload, o = download(False)
    print(l, len(payload), o)

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
