import json
from collections import OrderedDict
import pprint
import sys
import glob
from argparse import ArgumentParser

def get_option(log_file):
    argparser = ArgumentParser()
    argparser.add_argument('-f', '--logFile', type=str, default=log_file)
    return argparser.parse_args()



def main():
    logfile = sorted(glob.glob("ASTREAM_LOGS/ASTREAM_*"))[-1]
    args = get_option(logfile)

    with open(args.logFile, 'r') as f:
        log_dict = json.loads(f.readline(), object_pairs_hook=OrderedDict)

    # calc bufratio
    play_duration = log_dict['video_metadata']['playback_duration']
    total_stall_duration = log_dict['playback_info']['interruptions']['total_duration']
    bufratio = total_stall_duration / (play_duration + total_stall_duration)




if __name__ == "__main__":
    main()
