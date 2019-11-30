#!/bin/bash
 
set -eux

SCRIPT_DIR=$(cd $(dirname $0); pwd)

PROTOCOL=""
PORT="4443"
IP="dash.localdomain"

while getopts "p:i:b:d:l:" optKey; do
    case "$optKey" in
        p)
            if [ ${OPTARG} = "h3" ]; then
                PROTOCOL="-pro h3"
                PORT="6666"
            fi
            ;;
        i)
            IP=${OPTARG}
            ;;
        
        b)
            BW=${OPTARG}
            ;;
        
        d)
            DELAY=${OPTARG}
            ;;
        
        l)
            LOSS=${OPTARG}
            ;;

        *)
            ;;
    esac
done

python3 ${SCRIPT_DIR}/main.py --MPD https://${IP}:${PORT}/bunny_2s/bbb_short.mpd ${PROTOCOL} -b ${BW} -d ${DELAY} -l ${LOSS}


