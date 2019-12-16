import json
from collections import OrderedDict
import pprint
import sys
import glob
from argparse import ArgumentParser
import os

def get_option(log_file, ssim_file, n):
    argparser = ArgumentParser()
    argparser.add_argument('-l', '--logFile', type=str, default=log_file)
    argparser.add_argument('-s', '--ssimFile', type=str, default=ssim_file)
    argparser.add_argument('-n', '--num', type=int, default=n)
    return argparser.parse_args()

def parse_maximum_layer(log_dict, n):
    layer_of_segments = [[] for _ in range(n)]
    for segment in log_dict['segment_info']:
        _, _, seg, lay = segment[0].split('-')
        seg_ind = int(seg.split('.')[-1][3:])
        layer = int(lay.split('.')[0][1:])
        layer_of_segments[seg_ind].append(layer)
    max_layer = [0] * n
    for i in range(n):
        l = sorted(layer_of_segments[i])
        prev = -1
        for j in l:
            if j == prev + 1:
                max_layer[i] = j
            else:
                max_layer[i] = prev
                break
            prev = j

    return max_layer

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

def make_layer_str(log_dict):
    n = log_dict['segment_number']
    layer_of_segments = parse_maximum_layer(log_dict, n)
    s = ''
    for h in reversed(range(4)):
        for layer in layer_of_segments:
            if layer >= h:
                s += '#'
            else:
                s += ' '
        s += "\n"
    for i in range(n):
        if i % 10 == 0:
            s += '.'
        else:
            s += ' '
    s += "\n"
    return s


def generate_stat(logFile, ssimFile):
        print("logfile: ", logFile)
        print("ssimfile: ", ssimFile)


        with open(logFile, 'r') as f:
            log_dict = json.loads(f.readline(), object_pairs_hook=OrderedDict)

        with open(ssimFile, 'r') as f_ssim:
            ssim_dict = json.loads(f_ssim.readline())

        with open('{}/results/result_{}'.format(current_dir, logFile.split('/')[-1].replace('json', 'txt')), 'w') as f_result:
            f_result.write('proto: {}\nloss: {}\ndelay: {}\nbw: {}\nmpd: {}\nsvc_a: {}\nsvc_b: {}\nbuffer: {}\nalgor: {}\n'.format(log_dict['protocol'], log_dict['loss'], log_dict['delay'], log_dict['bandwidth'], log_dict['mpd'], log_dict['SVC_A'], log_dict['SVC_B'], log_dict['buffer_size'], log_dict['algor']))
            f_result.write("bufratio: {}\n".format(calc_bufratio(log_dict)))
            f_result.write("average ssim: {}\n".format(calc_average_ssim(log_dict, ssim_dict)))
            f_result.write(make_layer_str(log_dict))


current_dir = os.path.dirname(os.path.abspath(__file__))

def main():
    logfiles = sorted(glob.glob(current_dir + "/ASTREAM_LOGS/ASTREAM_*"))
    ssimfiles = sorted(glob.glob(current_dir + "/ssims/ssim_*"))
    print(logfiles[-1])
    print(current_dir)
    print(ssimfiles[-1])
    args = get_option(logfiles[-1], ssimfiles[-1], 1)
    generate_stat(args.logFile, args.ssimFile)


if __name__ == "__main__":
    main()
