import json
from collections import OrderedDict
import pprint
import sys
import glob
from argparse import ArgumentParser
import os
from pathlib import Path

frame_per_segs = 48

def get_option(log_file, ssim_file, frame_ssim_file, n):
    argparser = ArgumentParser()
    argparser.add_argument('-l', '--logFile', type=str, default=log_file)
    argparser.add_argument('-s', '--ssimFile', type=str, default=ssim_file)
    argparser.add_argument('-f', '--frameSsimFile', type=str, default=frame_ssim_file)
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

def calc_maximum_frame_layer(log_dict):
    n = log_dict['segment_number']
    max_frame_of_segments = [[0] * frame_per_segs for _ in range(n)]
    layer_of_segments = [[] for _ in range(n)]

    for segment in log_dict['segment_info']:
        _, _, seg, lay = segment[0].split('-')
        seg_ind = int(seg.split('.')[-1][3:])
        layer = int(lay.split('.')[0][1:])

        loss_range = int(segment[4])

        layer_of_segments[seg_ind].append((layer, loss_range))

    from operator import itemgetter
    for i in range(n):
        l = sorted(layer_of_segments[i])
        if len(l) == 1:
            continue
        for layer, loss_range in l:
            for j in range(frame_per_segs):
                if j < loss_range:
                    if layer - max_frame_of_segments[i][j] <= 1:
                        max_frame_of_segments[i][j] = layer
    return max_frame_of_segments


def calc_frame_average_ssim(log_dict, frame_ssim_list):
    n = log_dict['segment_number']
    s = 0
    maximum_frame_layer = calc_maximum_frame_layer(log_dict)
    for i in range(n):
        for j, M in enumerate(maximum_frame_layer[i]): # ma_f_l = [3,3,3,2,2,1,0]
            s += frame_ssim_list[frame_per_segs * i + j][M]
    return s / (n * frame_per_segs)

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

def calc_ssim(log_dict, ssim_dict, frame_ssim_list):
    if log_dict['reliability'] == 'unreliable':
        return calc_frame_average_ssim(log_dict, frame_ssim_list)
    else:
        return calc_average_ssim(log_dict, ssim_dict)

def calc_adjusted_ssim(log_dict, ssim):
    n = log_dict['segment_number']
    if 'interruptions' in log_dict['playback_info']:
        if 'total_duration' in log_dict['playback_info']['interruptions']:
            inter = log_dict['playback_info']['interruptions']['total_duration']
            frames = (frame_per_segs / 2) * inter
            return ssim * (n * frame_per_segs / (n * frame_per_segs + frames))
    return ssim


def generate_stat(logFile, ssimFile, frame_ssim_file):
        print("logfile: ", logFile)
        print("ssimfile: ", ssimFile)


        with open(logFile, 'r') as f:
            log_dict = json.loads(f.readline(), object_pairs_hook=OrderedDict)
            if 'timeout' in log_dict:
                print('exclude timeout result exiting...')
                sys.exit(0)

        with open(ssimFile, 'r') as f_ssim:
            ssim_dict = json.loads(f_ssim.readline())

        with open(frame_ssim_file, 'r') as f_framessim:
            frame_ssim_list = json.loads(f_framessim.readline())

        target_dir = str(sorted(filter(Path.is_dir, Path('.').glob('results/*')))[-1])
        if target_dir.split('/')[-1] > logFile[8:-5]:
            raise RuntimeError('invalid result log file')

        result_file = '{}/result_{}'.format(target_dir, logFile.split('/')[-1].replace('json', 'txt'))
        with open(result_file, 'w') as f_result:
            f_result.write('proto: {}\nloss: {}\ndelay: {}\nbw: {}\nmpd: {}\nsvc_a: {}\nsvc_b: {}\nbuffer: {}\nalgor: {}\n'.format(log_dict['protocol'], log_dict['loss'], log_dict['delay'], log_dict['bandwidth'], log_dict['mpd'], log_dict['SVC_A'], log_dict['SVC_B'], log_dict['buffer_size'], log_dict['algor']))
            f_result.write("reliability: {}\n".format(log_dict['reliability']))
            f_result.write("trace: {}\n".format(log_dict['trace']))
            f_result.write("bufratio: {}\n".format(calc_bufratio(log_dict)))
            ssim = calc_ssim(log_dict, ssim_dict, frame_ssim_list)
            f_result.write("average ssim: {}\n".format(ssim))
            f_result.write("assim: {}\n".format(calc_adjusted_ssim(log_dict, ssim)))
            f_result.write(make_layer_str(log_dict))
        
        os.chown(result_file, 1000, 1000)


current_dir = os.path.dirname(os.path.abspath(__file__))


def main():
    logfiles = sorted(glob.glob(current_dir + "/ASTREAM_LOGS/ASTREAM_*"))
    ssimfiles = sorted(glob.glob(current_dir + "/ssims/ssim_BBB.json"))
    frame_ssim_files = sorted(glob.glob(current_dir + "/ssims/ssim_frame_BBB.json"))
    print(logfiles[-1])
    print(current_dir)
    print(ssimfiles[-1])
    print(frame_ssim_files[-1])
    args = get_option(logfiles[-1], ssimfiles[-1], frame_ssim_files[-1], 1)
    generate_stat(args.logFile, args.ssimFile, args.frameSsimFile)


if __name__ == "__main__":
    main()
