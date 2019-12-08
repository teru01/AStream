package main

import "C"

import (
	"bytes"
	"crypto/tls"
	"encoding/binary"
	"fmt"
	"io"
	"net/http"
	"unsafe"

	"golang.org/x/net/http2"
)

var client *http.Client

func h2client(addr string) []byte {
	if client == nil {
		client = &http.Client{
			Transport: &http2.Transport{
				TLSClientConfig: &tls.Config{
					InsecureSkipVerify: true,
				},
			},
		}
	}
	fmt.Printf("golang: GET %s\n", addr)
	resp, err := client.Get(addr)
	if err != nil {
		panic(err)
	}
	buffer := &bytes.Buffer{}
	_, err = io.Copy(buffer, resp.Body)
	if err != nil {
		panic(err)
	}
	return buffer.Bytes()
}

//export H2client
func H2client(addr *C.char) unsafe.Pointer {
	s := C.GoString(addr)
	resp := h2client(s)
	length := make([]byte, 8)
	binary.LittleEndian.PutUint64(length, uint64(len(resp)))
	return C.CBytes(append(length, resp...))
}

func main() {}
