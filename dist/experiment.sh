set -eux

ssh lab2 sudo tc qdisc add dev enp0s25 root handle 1:0 tbf rate 20mbit burst 80kb limit 800kb

# loss_rates=(0.08 0.16 0.32 0.64 1.28 2.56 5.12)
loss_rates=(2.56 5.12)
for i in "${loss_rates[@]}"; do
    ssh lab2 sudo tc qdisc add dev enp0s25 parent 1:1 handle 10:1 netem loss $i%
    python main.py --MPD https://dash.localdomain:6666/bunny_2s/bbb.mpd -p basic -pro h3
    python main.py --MPD https://dash.localdomain:4443/bunny_2s/bbb.mpd -p basic
    ssh lab2 sudo tc qdisc del dev enp0s25 parent 1:1
done

ssh lab2 sudo tc qdisc del dev enp0s25 root
