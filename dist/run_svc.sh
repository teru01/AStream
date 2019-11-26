SCRIPT_DIR=$(cd $(dirname $0); pwd)

if [ $1 = "h3" ]; then
    python ${SCRIPT_DIR}/main.py --MPD https://dash.localdomain:6666/720p/BBB-I-720p_short.mpd -p svc -pro h3
else
    python ${SCRIPT_DIR}/main.py --MPD https://dash.localdomain:4443/720p/BBB-I-720p_short.mpd -p svc
fi
