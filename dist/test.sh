# reset
ssh lab2 sudo tc qdisc del dev enp0s25 root

ssh lab2 sudo tc qdisc add dev enp0s25 root handle 1:0 tbf rate 20mbit burst 80kb limit 800kb

loss_rates=(0.16 0.33)
for i in "${loss_rates[@]}"; do
    ssh lab2 sudo tc qdisc add dev enp0s25 parent 1:0 handle 10: netem delay 30ms loss $i%

    echo "loss rate: " $i
    sleep 1

    ssh lab2 sudo tc qdisc del dev enp0s25 parent 1:0
done

ssh lab2 sudo tc qdisc del dev enp0s25 root
