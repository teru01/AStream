AStream: A rate adaptaion model for DASH
==================
AStream is a Python based emulated video player to evalutae the perfomance of the DASH bitrate adaptaion algorithms.


Rate Adaptatation Algorithms Supported
--------------------------------------
1. Basic Adaptation
2. Segment Aware Rate Adaptation (SARA): Our algorithm
3. Buffer-Based Rate Adaptation (Netflix): This is based on the algorithm presented in the paper. 
   Te-Yuan Huang, Ramesh Johari, Nick McKeown, Matthew Trunnell, and Mark Watson. 2014. A buffer-based approach to rate adaptation: evidence from a large video streaming service. In Proceedings of the 2014 ACM conference on SIGCOMM (SIGCOMM '14). ACM, New York, NY, USA, 187-198. DOI=10.1145/2619239.2626296 http://doi.acm.org/10.1145/2619239.2626296

Logs
----

Buffer Logs:

1. Epoch time
2. Current Playback Time
3. Current Buffer Size (in segments)
4. Current Playback State

Playback Logs:

1. Epoch time
2. Playback time
3. Segment Number
4. Segment Size
5. Playback Bitrate 
6. Segment Size 
7. Segment Duration
8. Weighted harmonic mean average download rate

