import glob
import os
import json
from argparse import ArgumentParser
import csv

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
    print(current_dir, options.videoname)
    print('processing {}'.format(files))
    frame_per_seg = 48
    ssim_list = [[0, 0, 0, 0] for _ in range(14315)]
    for file in files:
        with open(file, 'r') as f:
            layer = int(file.split('.')[-2][-1])
            ssim = 0
            csvreader = csv.reader(f, delimiter='\t')
            for line in csvreader:
                line = list(map(lambda x: x.strip(), line))
                if len(line) > 0 and line[0].isdecimal():
                    frame_ind = int(line[0].strip()) 
                    print(frame_ind)
                    ssim_list[frame_ind][layer] = float(line[-2].strip())

    with open('{}/ssim_frame_{}.json'.format(current_dir, options.videoname), 'w') as j:
        j.write(json.dumps(ssim_list))

if __name__ == "__main__":
    main()
