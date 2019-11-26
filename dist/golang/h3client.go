package main

import "C"
import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"encoding/binary"
	"fmt"
	"io"
	"net/http"
	"unsafe"

	"github.com/lucas-clemente/quic-go/http3"
)

var hclient *http.Client

func h3client(addr string) []byte {
	pool, err := x509.SystemCertPool()
	if err != nil {
		panic(err)
	}

	roundTripper := &http3.RoundTripper{
		TLSClientConfig: &tls.Config{
			RootCAs:            pool,
			InsecureSkipVerify: true,
		},
	}
	if hclient == nil {
		hclient = &http.Client{
			Transport: roundTripper,
		}
	}
	fmt.Printf("golang: GET %s\n", addr)
	rsp, err := hclient.Get(addr) // 以前のコネクションを使いまわしたい
	if err != nil {
		panic(err)
	}
	body := &bytes.Buffer{}
	_, err = io.Copy(body, rsp.Body)
	if err != nil {
		fmt.Println(err.Error())
	}
	return body.Bytes()
}

//export H3client
func H3client(addr *C.char) unsafe.Pointer {
	s := C.GoString(addr)
	resp := h3client(s)
	length := make([]byte, 8)
	binary.LittleEndian.PutUint64(length, uint64(len(resp)))
	return C.CBytes(append(length, resp...))
}

func main() {}
