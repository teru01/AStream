import urllib
from ctypes import *
import sys
import threading
import time
import json
import random
import datetime
import os
import threading

lib = cdll.LoadLibrary("./h3client.so")
client = lib.H3client

client.argtypes = [c_char_p, c_int]
client.restype = POINTER(c_ubyte*16)

def download(unreliable, url, results):
    if unreliable:
        flag = 1
    else:
        flag = 0
    ptr = client(url.encode('utf8'), flag)
    length = int.from_bytes(ptr.contents[:8], byteorder="little")
    if length == 0:
        return
    validOffset = int.from_bytes(ptr.contents[8:16], byteorder="little")
    data = bytes(cast(ptr, POINTER(c_ubyte*(16 + length))).contents[16:])
    results.extend([data, validOffset])


def main():
    times = int(sys.argv[1])
    reliability = sys.argv[2]
    ip = sys.argv[3]
    loss = float(sys.argv[4])
    delay = int(sys.argv[5]) * 4
    result_dir = sys.argv[6]

    if reliability == 'unreliable':
        unreliable = True
    else:
        unreliable = False
    result_dict = {'loss': [], 'delay': [], 'reliability': [], 'time': [], 'offsets': []}
    i = 0
    while i < times:
        url = "https://{}:6666/720p/BBB-I-720p.seg7-L1.svc".format(ip)
        try:
            results = []
            start = time.time()
            download(unreliable, url, results)
            benchmark_time = time.time() - start
            if len(results) == 0:
                continue
            _, v = results
            print("******offset********: ", v)
            result_dict['loss'].append(loss)
            result_dict['delay'].append(str(delay) + 'ms')
            result_dict['reliability'].append(reliability)
            result_dict['time'].append(benchmark_time)
            result_dict['offsets'].append(v)
            i += 1
        except:
            continue

    file = result_dir + '/bench_{}'.format(datetime.datetime.today().strftime("%Y-%m-%d.%H_%M_%S"))
    with open(file, 'w', ) as f:
        f.write(json.dumps(result_dict))
    os.chmod(file, 0o777)

def my_sleep():
    time.sleep(10)

if __name__ == "__main__":
    main()

