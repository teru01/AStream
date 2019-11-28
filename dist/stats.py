import json
from collections import OrderedDict
import pprint
import sys
import glob
from argparse import ArgumentParser
import os

def get_option(log_file, ssim_file):
    argparser = ArgumentParser()
    argparser.add_argument('-l', '--logFile', type=str, default=log_file)
    argparser.add_argument('-s', '--ssimFile', type=str, default=ssim_file)
    return argparser.parse_args()

def parse_maximum_layer(log_dict, n):
    layer_of_segments = [0] * n
    for segment in log_dict['segment_info']:
        _, _, seg, lay = segment[0].split('-')
        seg_ind = int(seg.split('.')[-1][3:])
        layer = int(lay.split('.')[0][1:])
        layer_of_segments[seg_ind] = max(layer_of_segments[seg_ind], layer)
    return layer_of_segments

def calc_average_ssim(log_dict, ssim_dict):
    n = log_dict['segment_number']
    layer_of_segments = parse_maximum_layer(log_dict, n)
    s = 0
    for i in range(n):
        s += ssim_dict[i]["L" + str(layer_of_segments[i])]
    return s / n

def calc_bufratio(log_dict):
    play_duration = log_dict['video_metadata']['playback_duration']
    total_stall_duration = log_dict['playback_info']['interruptions']['total_duration']
    return total_stall_duration / (play_duration + total_stall_duration)

def print_layer(log_dict):
    n = log_dict['segment_number']
    layer_of_segments = parse_maximum_layer(log_dict, n)
    for h in reversed(range(4)):
        for layer in layer_of_segments:
            if layer >= h:
                print('#', end="")
            else:
                print(' ', end="")
        print("\n", end="")
    for i in range(n):
        if i % 10 == 0:
            print('.', end="")
        else:
            print(' ', end="")
    print("\n", end="")

def main():
    current_dir = os.path.dirname(__file__)
    print(__file__)
    logfile = sorted(glob.glob(current_dir + "./ASTREAM_LOGS/ASTREAM_*"))[-1]
    ssimfile = sorted(glob.glob(current_dir + "./ssims/ssim_*"))[-1]
    args = get_option(logfile, ssimfile)

    print("logfile: ", args.logFile)
    print("ssimfile: ", args.ssimFile)

    with open(args.logFile, 'r') as f:
        log_dict = json.loads(f.readline(), object_pairs_hook=OrderedDict)

    with open(args.ssimFile, 'r') as f_ssim:
        ssim_dict = json.loads(f_ssim.readline())

    print("bufratio: ", calc_bufratio(log_dict))
    print("average ssim: ", calc_average_ssim(log_dict, ssim_dict))
    print_layer(log_dict)

if __name__ == "__main__":
    main()
