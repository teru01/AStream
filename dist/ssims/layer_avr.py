import json


with open('ssim_frame_BBB.json') as f:
    data = json.loads(f.readline())
    res = 0
    c = 0
    for item in data[:90 * 48]:
        c += 1
        res += item[0]
    print(c)
    print(res / c)
