if [ $1 = "h3" ]; then
    python3 main.py --MPD https://dash.localdomain:6666/bunny_2s/bbb_single.mpd -p basic -pro h3
else
    python3 main.py --MPD https://dash.localdomain:4443/bunny_2s/bbb_single.mpd -p basic
fi
