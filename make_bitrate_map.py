# coding: utf-8
with open('bbb.mpd', 'r') as f:
    bw = []
    bi = []
    flg = False
    for l in f.readlines():
        if "bandwidth" in l:
            bw.append(l.split('"')[-2])
            flg = True
        if flg and "SegmentURL" in l:
            b = l.split('"')[-2].split('/')[0].split("_")[-1][:-4]
            bi.append(b)
            flg = False
    d = {p: q for p, q in zip(bw, bi)}
    print(d)
    
