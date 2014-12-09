# The configuration file for the AStream module
# create logger
LOG_NAME = 'astream_log'
LOG_LEVEL = None
# Set '-' to print to screen
LOG_FILENAME = 'DASH_PLAYBACK_LOG'
# Set
LOG = None

# Constants for the Buffer in the Weighted adaptation scheme (in segments)
INITIAL_BUFFER_COUNT = 2
ALPHA_BUFFER_COUNT = 5
BETA_BUFFER_COUNT = 10

# For ping.py
PING_PACKETS = 10
ping_option_nb_pkts = PING_PACKETS
rtt_match = None
rtt_pattern = None
index_rtt_min = None
index_rtt_avg = None
index_rtt_max = None
RTT = False