set -eux
SCRIPT_DIR=$(cd $(dirname $0); pwd)

# reset
ssh lab2 sudo tc qdisc del dev enp0s25 root

ssh lab2 sudo tc qdisc add dev enp0s25 root handle 1:0 tbf rate 20mbit burst 80kb limit 800kb

# loss_rates=(0.08 0.16 0.32 0.64 1.28 2.56 5.12)
loss_rates=(0.16 5.12)
for i in "${loss_rates[@]}"; do
    ssh lab2 sudo tc qdisc add dev enp0s25 parent 1:0 handle 10: netem delay 30ms loss $i%

    python3 ${SCRIPT_DIR}/main.py --MPD https://dash.localdomain:6666/720p/BBB-I-720p_short.mpd -p svc -pro h3
    python3 ${SCRIPT_DIR}/main.py --MPD https://dash.localdomain:4443/720p/BBB-I-720p_short.mpd -p svc

    ssh lab2 sudo tc qdisc del dev enp0s25 parent 1:0
done

ssh lab2 sudo tc qdisc del dev enp0s25 root
