package main

import "C"
import (
	"bytes"
	"crypto/tls"
	"encoding/binary"
	"fmt"
	"net/http"
	"unsafe"
	"strconv"
	"github.com/lucas-clemente/quic-go/http3"
	"github.com/lucas-clemente/quic-go"
)

var hclient *http.Client
const FRAMEPERSEG = 48

func h3client(addr string, unreliable bool) ([]byte, int64) {
	if hclient == nil {
		hclient = &http.Client{
			Transport: &http3.RoundTripper{
				TLSClientConfig: &tls.Config{
					InsecureSkipVerify: true,
				},
			},
		}
	}
	fmt.Printf("golang: GET %s\n", addr)
	rsp, err := http3.GetWithReliability(hclient, addr, unreliable) // 以前のコネクションを使いまわしたい
	if err != nil {
		panic(err)
	}
	vbuf := &bytes.Buffer{}
	body, _ := rsp.Body.(*http3.Body)
	_, lossRange, err := http3.Copy(vbuf, body, rsp)
	fmt.Println(lossRange)
	layer, err := strconv.Atoi(string(addr[len(addr) - 5]))
	if err != nil {
		panic(err)
	}

	var validOffset int64
	if unreliable && layer > 0 {
		// EL
		validOffset = calcValidOffset(lossRange, vbuf.Bytes())
	} else {
		// BL
		validOffset = FRAMEPERSEG - 1
	}
	return vbuf.Bytes(), validOffset
}

//export H3client
func H3client(addr *C.char, flag C.int) unsafe.Pointer {
	s := C.GoString(addr)
	var unreliable bool
	if flag == 1 {
		unreliable = true
	} else {
		unreliable = false
	}
	resp, validOffset := h3client(s, unreliable)
	length := make([]byte, 8)
	offsetBuf := make([]byte, 8)
	binary.LittleEndian.PutUint64(length, uint64(len(resp)))
	binary.PutVarint(offsetBuf, validOffset)
	return C.CBytes(append(append(length, offsetBuf...), resp...))
}

func calcValidOffset(lossRange []quic.ByteRange, payload []byte) int64 {
	if len(lossRange) == 0 {
		return FRAMEPERSEG - 1
	}
	if lossRange[0].Start == 0 {
		// 先頭バイトがロスしてる
		return -1
	}
	data := payload[:lossRange[0].Start]
	return int64(len(bytes.Split(data, []byte{0x0, 0x1}))-3) // 利用できる最大のフレームオフセット
}


func main() {}
