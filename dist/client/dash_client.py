#!/usr/local/bin/python
"""
Author:            Parikshit Juluri
Contact:           pjuluri@umkc.edu
Testing:
    import dash_client
    mpd_file = <MPD_FILE>
    dash_client.playback_duration(mpd_file, 'http://198.248.242.16:8005/')

    From commandline:
    python dash_client.py -m "http://198.248.242.16:8006/media/mpd/x4ukwHdACDw.mpd" -p "all"
    python dash_client.py -m "http://127.0.0.1:8000/media/mpd/x4ukwHdACDw.mpd" -p "basic"

"""

from . import read_mpd
import urllib.parse
import urllib.request, urllib.error, urllib.parse
import random
import os
import sys
import errno
import timeit
import http.client
from string import ascii_letters, digits
from argparse import ArgumentParser
from multiprocessing import Process, Queue
from collections import defaultdict
from .adaptation import basic_dash, basic_dash2, weighted_dash, netflix_dash
from .adaptation.adaptation import WeightedMean
from . import config_dash
from . import dash_buffer
from .configure_log_file import configure_log_file, write_json
import time
from ctypes import *
import threading

# Constants
DEFAULT_PLAYBACK = 'BASIC'
DOWNLOAD_CHUNK = 1024

unreliable_mode = False

# Globals for arg parser with the default values
# Not sure if this is the correct way ....
MPD = None
LIST = False
PLAYBACK = DEFAULT_PLAYBACK
DOWNLOAD = False
SEGMENT_LIMIT = None
PROTOCOL = "h2"

http_connection = None

class DashPlayback:
    """
    Audio[bandwidth] : {duration, url_list}
    Video[bandwidth] : {duration, url_list}
    """
    def __init__(self):

        self.min_buffer_time = None
        self.playback_duration = None
        self.audio = dict()
        self.video = dict()


class Connection:
    def __init__(self, proto):
        libh3 = cdll.LoadLibrary(os.path.join(os.path.dirname(__file__), "../golang/h3client.so"))
        libh2 = cdll.LoadLibrary(os.path.join(os.path.dirname(__file__), "../golang/h2client.so"))
        if proto == "h2":
            self.request = libh2.H2client
        elif proto == "h3":
            self.request = libh3.H3client
        else:
            print("undefined protocol")
            sys.exit(0)
        self.request.argtypes = [c_char_p, c_int]
        self.request.restype = POINTER(c_ubyte*16)

    def read(self, url, unreliable):
        if unreliable:
            flag = 1
        else:
            flag = 0
        ptr = self.request(url.encode('utf8'), flag)
        length = int.from_bytes(ptr.contents[:8], byteorder="little")
        if length == 0:
            config_dash.JSON_HANDLE['timeout'] = True
            return
        validOffset = int.from_bytes(ptr.contents[8:16], byteorder="little")
        data = bytes(cast(ptr, POINTER(c_ubyte*(16 + length))).contents[16:])
        return data, validOffset

def get_mpd(url):
    """ Module to download the MPD from the URL and save it to file"""
    print(url)
    try:
        connection = http_connection
    except urllib.error.HTTPError as error:
        config_dash.LOG.error("Unable to download MPD file HTTP Error: %s" % error.code)
        return None
    except urllib.error.URLError:
        error_message = "URLError. Unable to reach Server.Check if Server active"
        config_dash.LOG.error(error_message)
        print(error_message)
        return None
    except IOError as xxx_todo_changeme:
        http.client.HTTPException = xxx_todo_changeme
        message = "Unable to , file_identifierdownload MPD file HTTP Error."
        config_dash.LOG.error(message)
        return None
    
    mpd_data, _ = connection.read(url, False)
    mpd_file = url.split('/')[-1]
    mpd_file_handle = open(mpd_file, 'wb')
    mpd_file_handle.write(mpd_data)
    mpd_file_handle.close()
    config_dash.LOG.info("Downloaded the MPD file {}".format(mpd_file))
    return mpd_file


def get_bandwidth(data, duration):
    """ Module to determine the bandwidth for a segment
    download"""
    return data * 8/duration


def get_domain_name(url):
    """ Module to obtain the domain name from the URL
        From : http://stackoverflow.com/questions/9626535/get-domain-name-from-url
    """
    parsed_uri = urllib.parse.urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    return domain


def id_generator(id_size=6):
    """ Module to create a random string with uppercase 
        and digits.
    """
    return 'TEMP_' + ''.join(random.choice(ascii_letters+digits) for _ in range(id_size))


def download_segment(segment_url, dash_folder, unreliable):
    """ Module to download the segment """
    try:
        connection = http_connection
    except urllib.error.HTTPError as error:
        config_dash.LOG.error("Unable to download DASH Segment {} HTTP Error:{} ".format(segment_url, str(error.code)))
        return None
    parsed_uri = urllib.parse.urlparse(segment_url)
    segment_path = '{uri.path}'.format(uri=parsed_uri)
    while segment_path.startswith('/'):
        segment_path = segment_path[1:]        
    segment_filename = os.path.join(dash_folder, os.path.basename(segment_path))
    make_sure_path_exists(os.path.dirname(segment_filename))
    segment_file_handle = open(segment_filename, 'wb')

    segment_data, valid_offset_from_head = connection.read(segment_url, unreliable)
    segment_file_handle.write(segment_data)
    segment_file_handle.close()
    #print "segment size = {}".format(segment_size)
    #print "segment filename = {}".format(segment_filename)
    return len(segment_data), segment_filename, segment_data, valid_offset_from_head


def get_media_all(domain, media_info, file_identifier, done_queue):
    """ Download the media from the list of URL's in media
    """
    bandwidth, media_dict = media_info
    media = media_dict[bandwidth]
    media_start_time = timeit.default_timer()
    for segment in [media.initialization] + media.url_list:
        start_time = timeit.default_timer()
        segment_url = urllib.parse.urljoin(domain, segment)
        _, segment_file, _, _ = download_segment(segment_url, file_identifier)
        elapsed = timeit.default_timer() - start_time
        if segment_file:
            done_queue.put((bandwidth, segment_url, elapsed))
    media_download_time = timeit.default_timer() - media_start_time
    done_queue.put((bandwidth, 'STOP', media_download_time))
    return None


def make_sure_path_exists(path):
    """ Module to make sure the path exists if not create it
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise


def print_representations(dp_object):
    """ Module to print the representations"""
    print("The DASH media has the following video representations/bitrates")
    for bandwidth in dp_object.video:
        print(bandwidth)


def start_playback_smart(dp_object, domain, playback_type=None, download=False, video_segment_duration=None):
    """ Module that downloads the MPD-FIle and download
        all the representations of the Module to download
        the MPEG-DASH media.
        Example: start_playback_smart(dp_object, domain, "SMART", DOWNLOAD, video_segment_duration)

        :param dp_object:       The DASH-playback object
        :param domain:          The domain name of the server (The segment URLS are domain + relative_address)
        :param playback_type:   The type of playback
                                1. 'BASIC' - The basic adapataion scheme
                                2. 'SARA' - Segment Aware Rate Adaptation
                                3. 'NETFLIX' - Buffer based adaptation used by Netflix
        :param download: Set to True if the segments are to be stored locally (Boolean). Default False
        :param video_segment_duration: Playback duratoin of each segment
        :return:
    """
    # Initialize the DASH buffer
    dash_player = dash_buffer.DashPlayer(dp_object.playback_duration, video_segment_duration)
    dash_player.start()
    # A folder to save the segments in
    file_identifier = id_generator()
    config_dash.LOG.info("The segments are stored in %s" % file_identifier)
    dp_list = defaultdict(defaultdict)
    # Creating a Dictionary of all that has the URLs for each segment and different bitrates
    bitrate_map = {str(v): str(k) for k, v in enumerate(sorted(map(int, dp_object.video.keys())))}
    for bitrate in dp_object.video:
        # Getting the URL list for each bitrate
        dp_object.video[bitrate] = read_mpd.get_url_list(dp_object.video[bitrate], video_segment_duration,
                                                         dp_object.playback_duration, bitrate, bitrate_map)

        if "$bitrate$" in dp_object.video[bitrate].initialization:
            dp_object.video[bitrate].initialization = dp_object.video[bitrate].initialization.replace(
                "$bitrate$", str(bitrate))
        media_urls = [dp_object.video[bitrate].initialization] + dp_object.video[bitrate].url_list
        for segment_count, segment_url in enumerate(media_urls, dp_object.video[bitrate].start):
            # segment_duration = dp_object.video[bitrate].segment_duration
            #print "segment url"
            #print segment_url
            # print(segment_url)
            dp_list[segment_count][bitrate] = segment_url
    bitrates = list(dp_object.video.keys())
    bitrates.sort()
    average_dwn_time = 0
    config_dash.JSON_HANDLE['segment_number'] = len(dp_list) - 1
    # with open("dp_list_svc.txt", "w") as f:
    #     for i, d in dp_list.items():
    #         f.write("{}: {}\n".format(i, d))
    # For basic adaptation
    previous_segment_times = []
    recent_download_sizes = []
    weighted_mean_object = None
    current_bitrate = bitrates[0]
    previous_bitrate = None
    total_downloaded = 0
    # Delay in terms of the number of segments
    delay = 0
    segment_duration = 0
    segment_size = segment_download_time = None
    # Netflix Variables
    average_segment_sizes = netflix_rate_map = None
    netflix_state = "INITIAL"
    # Start playback of all the segments
    delay = 0
    state = config_dash.SVC_STATE_INIT
    for segment_number, segment in enumerate(dp_list.values(), dp_object.video[current_bitrate].start):
        # dp_listは{int: dict}
        config_dash.LOG.info("Processing the segment {} : {}".format(segment_number, segment))
        # write_json()
        if not previous_bitrate:
            previous_bitrate = current_bitrate
        if SEGMENT_LIMIT:
            if not dash_player.segment_limit:
                dash_player.segment_limit = int(SEGMENT_LIMIT)
            if segment_number > int(SEGMENT_LIMIT):
                config_dash.LOG.info("Segment limit reached")
                break
        if segment_number == dp_object.video[bitrate].start:
            current_bitrate = bitrates[0]
        else:
            if playback_type.upper() == "SVC":
                max_safe_layer_id, _ = basic_dash2.basic_dash2("", bitrates, "", recent_download_sizes, previous_segment_times, current_bitrate)
                current_bitrate = bitrates[max_safe_layer_id]
                dl_threads = []
                for i in range(min(max_safe_layer_id + 2, len(bitrates))):
                    segment_url = urllib.parse.urljoin(domain, segment[bitrates[i]])
                    try:
                        if i == 0:
                            t = threading.Thread(target=download_wrapper, args=(segment_url,
                            file_identifier, previous_segment_times, recent_download_sizes,
                            current_bitrate, segment_number, video_segment_duration, dash_player, config_dash.SVC_BASE_LAYER, False)) # BLはreliable
                        else:
                            t = threading.Thread(target=download_wrapper, args=(segment_url,
                            file_identifier, previous_segment_times, recent_download_sizes,
                            current_bitrate, segment_number, video_segment_duration, dash_player, config_dash.SVC_EH_LAYER, unreliable_mode))
                        dl_threads.append(t)
                        # time.sleep(0.1)
                        t.start()
                    except RuntimeError as e:
                        # キューへの挿入ができなかった
                        pass
                        # config_dash.LOG.warning("")
                for th in dl_threads:
                    th.join()

                    if dash_player.buffer.qsize() > config_dash.SVC_THRESHOLD:
                        delay = dash_player.buffer.qsize() - config_dash.SVC_THRESHOLD


            else:
                config_dash.LOG.error("Unknown playback type:{}. Continuing with basic playback".format(playback_type))
                current_bitrate, average_dwn_time = basic_dash.basic_dash(segment_number, bitrates, average_dwn_time,
                                                                          segment_download_time, current_bitrate)

        # バッファが閾値を超えてるなら待機する。
        if delay:
            delay_start = time.time()
            config_dash.LOG.info("SLEEPING for {} seconds ".format(delay*video_segment_duration))
            while time.time() - delay_start < (delay * video_segment_duration):
                time.sleep(1)
            delay = 0

    # waiting for the player to finish playing
    while dash_player.playback_state not in dash_buffer.EXIT_STATES:
        time.sleep(1)
    # write_json()
    if not download:
        clean_files(file_identifier)

def highest_received_layer(seg_number, dash_player):
    seg = dash_player.buffer.search_segment(seg_number)
    # if seg == None:

    return len(seg['data']) - 1

# 評価に必要なもの: {'segment_no', 'max_layer: どの層までDLしたか'}
# EL取得に必要なもの: {'current_throughput'}
def download_wrapper(segment_url,
    file_identifier,
    previous_segment_times,
    recent_download_sizes,
    current_bitrate,
    segment_number,
    video_segment_duration,
    dash_player,
    segment_type,
    unreliable
    ):
    # DLと統計情報の更新、
    # return: download time
    start_time = timeit.default_timer()
    try:
        segment_size, segment_filename, payload, valid_frame_offset = download_segment(segment_url, file_identifier, unreliable)
        config_dash.LOG.info("Downloaded segment {}, segment_num: {}".format(segment_url.split('.')[-2:], segment_number))
    except IOError as e:
        config_dash.LOG.error("Unable to save segment %s" % e)
        return None
    segment_download_time = timeit.default_timer() - start_time
    previous_segment_times.append(segment_download_time)
    recent_download_sizes.append(segment_size)
    # Updating the JSON information
    segment_name = os.path.split(segment_url)[1]
    if "segment_info" not in config_dash.JSON_HANDLE:
        config_dash.JSON_HANDLE["segment_info"] = list()

    with open(config_dash.BUFFER_ANIME_FILENAME, 'a') as f_anime:
        layer = segment_filename.split('.')[-2][-2:]
        if layer == 'L0':
            f_anime.write(f"{segment_number-1} 0\n")
        elif layer == '16':
            f_anime.write(f"{segment_number-1} 1\n")
        elif layer == '32':
            f_anime.write(f"{segment_number-1} 2\n")
        elif layer == '48':
            f_anime.write(f"{segment_number-1} 3\n")
    if segment_type == config_dash.SVC_BASE_LAYER:
        # キューの末尾に追加
        segment_info = {'playback_length': video_segment_duration,
                        'size': [segment_size],
                        'bitrate': [current_bitrate],
                        'data': [segment_filename],
                        'URI': [segment_url],
                        'segment_number': segment_number}
        segment_duration = segment_info['playback_length']
        dash_player.write(segment_info)
    elif segment_type == config_dash.SVC_EH_LAYER:
        pass
        # キューから対応するセグメントを取り出し更新
        # with dash_player.buffer_lock:
        #     bl_segment = dash_player.buffer.search_segment(segment_number)
        #     if bl_segment == None:
        #         config_dash.LOG.info('segnum: {} not found'.format(segment_number))
        #         return
        #     bl_segment['size'].append(segment_size)
        #     bl_segment['bitrate'].append(current_bitrate)
        #     bl_segment['data'].append(segment_filename)
        #     bl_segment['URI'].append(segment_url)

    # valid_frames_from_head = 
    config_dash.JSON_HANDLE["segment_info"].append((segment_name, current_bitrate, segment_size,
                                                    segment_download_time, valid_frame_offset))
    config_dash.LOG.info("Downloaded %s. Size = %s in %s seconds" % (
        segment_url.split('.')[-2:], segment_size, str(segment_download_time)))

def get_segment_sizes(dp_object, segment_number):
    """ Module to get the segment sizes for the segment_number
    :param dp_object:
    :param segment_number:
    :return:
    """
    segment_sizes = dict([(bitrate, dp_object.video[bitrate].segment_sizes[segment_number]) for bitrate in dp_object.video])
    config_dash.LOG.debug("The segment sizes of {} are {}".format(segment_number, segment_sizes))
    return segment_sizes


def get_average_segment_sizes(dp_object):
    """
    Module to get the avearge segment sizes for each bitrate
    :param dp_object:
    :return: A dictionary of aveage segment sizes for each bitrate
    """
    average_segment_sizes = dict()
    for bitrate in dp_object.video:
        segment_sizes = dp_object.video[bitrate].segment_sizes
        segment_sizes = [float(i) for i in segment_sizes]
        try:
            average_segment_sizes[bitrate] = sum(segment_sizes)/len(segment_sizes)
        except ZeroDivisionError:
            average_segment_sizes[bitrate] = 0
    config_dash.LOG.info("The avearge segment size for is {}".format(list(average_segment_sizes.items())))
    return average_segment_sizes


def clean_files(folder_path):
    """
    :param folder_path: Local Folder to be deleted
    """
    if os.path.exists(folder_path):
        try:
            for video_file in os.listdir(folder_path):
                file_path = os.path.join(folder_path, video_file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            os.rmdir(folder_path)
        except OSError as e:
            config_dash.LOG.info("Unable to delete the folder {}. {}".format(folder_path, e))
        config_dash.LOG.info("Deleted the folder '{}' and its contents".format(folder_path))


def start_playback_all(dp_object, domain):
    """ Module that downloads the MPD-FIle and download all the representations of 
        the Module to download the MPEG-DASH media.
    """
    # audio_done_queue = Queue()
    video_done_queue = Queue()
    processes = []
    file_identifier = id_generator(6)
    config_dash.LOG.info("File Segments are in %s" % file_identifier)
    # for bitrate in dp_object.audio:
    #     # Get the list of URL's (relative location) for the audio
    #     dp_object.audio[bitrate] = read_mpd.get_url_list(bitrate, dp_object.audio[bitrate],
    #                                                      dp_object.playback_duration)
    #     # Create a new process to download the audio stream.
    #     # The domain + URL from the above list gives the
    #     # complete path
    #     # The fil-identifier is a random string used to
    #     # create  a temporary folder for current session
    #     # Audio-done queue is used to exchange information
    #     # between the process and the calling function.
    #     # 'STOP' is added to the queue to indicate the end
    #     # of the download of the sesson
    #     process = Process(target=get_media_all, args=(domain, (bitrate, dp_object.audio),
    #                                                   file_identifier, audio_done_queue))
    #     process.start()
    #     processes.append(process)

    for bitrate in dp_object.video:
        dp_object.video[bitrate] = read_mpd.get_url_list(bitrate, dp_object.video[bitrate],
                                                         dp_object.playback_duration,
                                                         dp_object.video[bitrate].segment_duration)
        # Same as download audio
        process = Process(target=get_media_all, args=(domain, (bitrate, dp_object.video),
                                                      file_identifier, video_done_queue))
        process.start()
        processes.append(process)
    for process in processes:
        process.join()
    count = 0
    for queue_values in iter(video_done_queue.get, None):
        bitrate, status, elapsed = queue_values
        if status == 'STOP':
            config_dash.LOG.critical("Completed download of %s in %f " % (bitrate, elapsed))
            count += 1
            if count == len(dp_object.video):
                # If the download of all the videos is done the stop the
                config_dash.LOG.critical("Finished download of all video segments")
                break


def create_arguments(parser):
    """ Adding arguments to the parser """
    parser.add_argument('-m', '--MPD',
                        help="Url to the MPD File")
    parser.add_argument('-l', '--LOSS',
                        help="packet loss")
    parser.add_argument('-p', '--PLAYBACK',
                        default=DEFAULT_PLAYBACK,
                        help="Playback type (basic, sara, netflix, or all)")
    parser.add_argument('-n', '--SEGMENT_LIMIT',
                        default=SEGMENT_LIMIT,
                        help="The Segment number limit")
    parser.add_argument('-d', '--DELAY', help="delay")
    parser.add_argument('-b', '--BANDWIDTH', help="bandwidth")
    parser.add_argument('-u', '--RELIABILITY', help="unreliable or not")
    parser.add_argument('-pro', '--PROTOCOL',
                        default="h2",
                        help="protocol[h2|h3]")


def main():
    global http_connection
    """ Main Program wrapper """
    # configure the log file
    # Create arguments
    parser = ArgumentParser(description='Process Client parameters')
    create_arguments(parser)
    args = parser.parse_args()
    globals().update(vars(args))

    http_connection = Connection(PROTOCOL)
    configure_log_file(playback_type=PLAYBACK.lower())
    config_dash.JSON_HANDLE['playback_type'] = PLAYBACK.lower()
    config_dash.JSON_HANDLE['loss'] = args.LOSS
    config_dash.JSON_HANDLE['delay'] = args.DELAY
    config_dash.JSON_HANDLE['bandwidth'] = args.BANDWIDTH
    config_dash.JSON_HANDLE['protocol'] = args.PROTOCOL
    config_dash.JSON_HANDLE['mpd'] = MPD
    config_dash.JSON_HANDLE['SVC_A'] = config_dash.SVC_A
    config_dash.JSON_HANDLE['SVC_B'] = config_dash.SVC_B
    config_dash.JSON_HANDLE['buffer_size'] = config_dash.SVC_THRESHOLD
    config_dash.JSON_HANDLE['algor'] = 'svc-naive-aggressive'
    config_dash.JSON_HANDLE['reliability'] = args.RELIABILITY
    config_dash.JSON_HANDLE['BASIC_UPPER_THRESHOLD'] = config_dash.BASIC_UPPER_THRESHOLD
    
    global unreliable_mode
    if args.RELIABILITY == 'unreliable':
        unreliable_mode = True
    else:
        unreliable_mode = False

    
    if not MPD:
        print("ERROR: Please provide the URL to the MPD file. Try Again..")
        return None
    config_dash.LOG.info('Downloading MPD file %s' % MPD)
    # Retrieve the MPD files for the video
    mpd_file = get_mpd(MPD)
    domain = get_domain_name(MPD)
    dp_object = DashPlayback()
    
    # Reading the MPD file created
    dp_object, video_segment_duration = read_mpd.read_mpd(mpd_file, dp_object)
    
    config_dash.LOG.info("The DASH media has %d video representations" % len(dp_object.video))
    if LIST:
        # Print the representations and EXIT
        print_representations(dp_object)
        return None
    if "all" in PLAYBACK.lower():
        if mpd_file:
            config_dash.LOG.critical("Start ALL Parallel PLayback")
            start_playback_all(dp_object, domain)
    elif "svc" in PLAYBACK.lower():
        config_dash.LOG.critical("Started Basic-DASH Playback")
        start_playback_smart(dp_object, domain, "SVC", DOWNLOAD, video_segment_duration)
    elif "basic" in PLAYBACK.lower():
        config_dash.LOG.critical("Started Basic-DASH Playback")
        start_playback_smart(dp_object, domain, "BASIC", DOWNLOAD, video_segment_duration)
    elif "sara" in PLAYBACK.lower():
        config_dash.LOG.critical("Started SARA-DASH Playback")
        start_playback_smart(dp_object, domain, "SMART", DOWNLOAD, video_segment_duration)
    elif "netflix" in PLAYBACK.lower():
        config_dash.LOG.critical("Started Netflix-DASH Playback")
        start_playback_smart(dp_object, domain, "NETFLIX", DOWNLOAD, video_segment_duration)
    else:
        config_dash.LOG.error("Unknown Playback parameter {}".format(PLAYBACK))
        return None

    write_json()


if __name__ == "__main__":
    sys.exit(main())
