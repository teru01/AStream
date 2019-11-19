if [ $1 = "h3" ]; then
    python main.py --MPD https://dash.localdomain:6666/bunny_2s/bbb.mpd -p basic -pro h3
else
    python main.py --MPD https://dash.localdomain:4443/bunny_2s/bbb.mpd -p basic
fi
