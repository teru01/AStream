import glob
import sys
import time

if len(sys.argv) == 1:
    f = sorted(glob.glob("ASTREAM_LOGS/BUFFER_ANIME_LOG*"))[-1]
else:
    f = sys.argv[1]

segs = [['.'] * 50 for _ in range(4)]

with open(f, 'r') as f_anime:
    for line in f_anime.readlines():
        x, y = map(int, line.split())
        segs[y][x] = '#'
        for row in reversed(segs):
            print("".join(row))
        time.sleep(1)
