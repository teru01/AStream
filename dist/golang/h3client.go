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
	"time"
	"context"
	"github.com/lucas-clemente/quic-go/http3"
	"github.com/lucas-clemente/quic-go"
)

var hclient *http.Client
const FRAMEPERSEG = 48

type frameRange struct {
	Start uint64
	End uint64
}

type Result struct {
	data []byte
	validRange []frameRange
}

func h3client(addr string, unreliable bool) Result {
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
	fmt.Println("lossRange: ", lossRange)
	layer, err := strconv.Atoi(string(addr[len(addr) - 5]))
	validRange := []frameRange{ frameRange{Start:0, End: FRAMEPERSEG}, frameRange{Start:FRAMEPERSEG, End: FRAMEPERSEG}}
	if err == nil {
		if unreliable && layer > 0 {
			// EL
			fmt.Println("datalen: ", len(vbuf.Bytes()))
			validRange = calcValidRange(lossRange, vbuf.Bytes())
		} 
		// else {
		// 	// BL
		// 	validRange = []frameRange{ frameRange{Start:0, End: FRAMEPERSEG+1}, frameRange{Start:FRAMEPERSEG, End: FRAMEPERSEG}}
		// }
	}
	fmt.Println(validRange)
	return Result{data: vbuf.Bytes(), validRange: validRange}
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
	ctx, cancel := context.WithTimeout(context.Background(), 20 * time.Second)
	defer cancel()

	ch := make(chan Result, 1)
	go func() {
		ch <- h3client(s, unreliable)
	}()
	select {
	case result := <-ch:
		resp := result.data
		validRange := result.validRange
		fmt.Println("validOffset: ", validRange)
		length := make([]byte, 8)
		headBegin := make([]byte, 8)
		headEnd := make([]byte, 8)
		tailBegin := make([]byte, 8)
		tailEnd := make([]byte, 8)
		binary.LittleEndian.PutUint64(length, uint64(len(resp)))
		binary.LittleEndian.PutUint64(headBegin, validRange[0].Start)
		binary.LittleEndian.PutUint64(headEnd, validRange[0].End)
		binary.LittleEndian.PutUint64(tailBegin, validRange[1].Start)
		binary.LittleEndian.PutUint64(tailEnd, validRange[1].End)
		fmt.Println("len ", len(resp))
		return C.CBytes(append(append(append(append(append(length, headBegin...), headEnd...), tailBegin...), tailEnd...) , resp...))
	case <- ctx.Done():
		fmt.Println("go timeout")
		buf := make([]byte, 40)
		return C.CBytes(buf)
	}
	return nil
}

// func calcValidOffset(lossRange []quic.ByteRange, payload []byte) uint64 {
// 	if len(lossRange) == 0 {
// 		return FRAMEPERSEG+1
// 	}
// 	if lossRange[0].Start == 0 {
// 		// 先頭バイトがロスしてる
// 		return 0
// 	}
// 	data := payload[:lossRange[0].Start]
// 	v := len(bytes.Split(data, []byte{0, 0, 0, 1})) - 2
// 	return uint64(v) // 利用できる最大のフレームオフセット
// }

func calcValidRange(lossRange []quic.ByteRange, payload []byte) []frameRange {
	result := make([]frameRange, 0)

	if len(lossRange) == 0 {
		return []frameRange{ frameRange{0, FRAMEPERSEG}, frameRange{FRAMEPERSEG, FRAMEPERSEG} }
	}
	if lossRange[0].Start == 0 {
		result = append(result, frameRange{0, 0})
	} else {
		data := payload[:lossRange[0].Start]
		v := uint64(len(bytes.Split(data, []byte{0, 0, 0, 1})) - 2)
		result = append(result, frameRange{0, v})
	}
	if int(lossRange[len(lossRange)-1].End) > len(payload)-1 {
		result = append(result, frameRange{FRAMEPERSEG, FRAMEPERSEG})
	} else{
		data := payload[lossRange[len(lossRange)-1].End:]
		v := uint64(len(bytes.Split(data, []byte{0, 0, 0, 1})) - 1)
		result = append(result, frameRange{FRAMEPERSEG-v, FRAMEPERSEG})
	}
	return result // 利用できる最大のフレームオフセット
}

func main() {}
