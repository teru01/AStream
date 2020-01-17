#!/bin/bash
 
set -eux

SCRIPT_DIR=$(cd $(dirname $0); pwd)

PROTOCOL=""
PORT="4443"
IP="dash.localdomain"
MPDPATH="720p/BBB-I-720p_short.mpd"
RELIABILITY="reliable"

while getopts "p:i:b:d:l:r:u:f:t:" optKey; do
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
        r)
            RESOLUTION=${OPTARG}
            if [ ${RESOLUTION} = "360" ]; then
                MPDPATH="BBB-360p/bbb_short.mpd"
            else
                MPDPATH="720p/BBB-I-720p_short.mpd"
            fi
            ;;
        u)
            RELIABILITY=${OPTARG}
            ;;
        f)
            BUFFERSIZE=${OPTARG}
            ;;
        t)
            TRACE=${OPTARG}
            ;;
        *)
            ;;
    esac
done

python3 ${SCRIPT_DIR}/main.py --MPD https://${IP}:${PORT}/${MPDPATH} -p svc ${PROTOCOL} -b ${BW} -d ${DELAY} -l ${LOSS} -u ${RELIABILITY} -f ${BUFFERSIZE} -t ${TRACE}


