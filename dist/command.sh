++ ssh lab2 sudo tc qdisc add dev enp0s25 root handle 1:0 tbf rate 20mbit burst 80kb limit 800kb
++ loss_rates=(2.56 5.12)
++ for i in '"${loss_rates[@]}"'
++ ssh lab2 sudo tc qdisc add dev enp0s25 parent 1:1 handle 10:1 netem loss 2.56%
++ python main.py --MPD https://dash.localdomain:6666/bunny_2s/bbb.mpd -p basic -pro h3
Traceback (most recent call last):
  File "main.py", line 3, in <module>
    dash_client.main()
  File "/Users/mirai/works/go/src/github.com/teru01/AStream/dist/client/dash_client.py", line 559, in main
    start_playback_smart(dp_object, domain, "BASIC", DOWNLOAD, video_segment_duration)
  File "/Users/mirai/works/go/src/github.com/teru01/AStream/dist/client/dash_client.py", line 352, in start_playback_smart
    time.sleep(1)
KeyboardInterrupt
