import glob
import os
import json
from argparse import ArgumentParser

def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_options(default='BBB'):
    argparser = ArgumentParser()
    argparser.add_argument('-n', '--videoname', default=default)
    return argparser.parse_args()

def main():
    current_dir = os.path.dirname(__file__)
    options = get_options()
    files = sorted(glob.glob('{}/*{}*.txt'.format(current_dir, options.videoname)))
    print('processing {}'.format(files))
    frame_per_seg = 48
    ssim_list = [{} for _ in range(500)]
    for file in files:
        with open(file, 'r') as f:
            layer = file.split('.')[-2][-1]
            num = 0
            ssim = 0
            segment_number = 0
            for ln, line in enumerate(f):
                elm = line.split()
                if len(elm) > 0 and elm[0].isdecimal():
                    frame_ind = int(elm[0])
                    num += 1
                    if is_float(elm[-1]):
                        ssim += float(elm[-1])
                    else:
                        ssim += float(elm[-2])
                    if num % frame_per_seg == 0:
                        num = 0
                        ssim_list[segment_number]['L' + layer] = ssim / frame_per_seg
                        ssim = 0
                        segment_number += 1
            if (frame_ind + frame_per_seg) // frame_per_seg == segment_number+1 and (frame_ind + 1) % frame_per_seg == num:
                print('finished to read {}'.format(f))
            else:
                raise RuntimeError('segnum: {}, num :{}'.format(segment_number, num))
    with open('{}/ssim_{}.json'.format(current_dir, options.videoname), 'w') as j:
        j.write(json.dumps(ssim_list))

if __name__ == "__main__":
    main()
