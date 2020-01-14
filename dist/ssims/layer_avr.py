import json


with open('ssim_BBB.json') as f:
    data = json.loads(f.readline())
    res = 0
    c = 0
    for item in data:
        if 'L0' in item:
            c += 1
            res += item['L0']
    print(res / c)
