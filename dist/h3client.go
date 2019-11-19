package main

import "C"

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"io"
	"net/http"

	"github.com/lucas-clemente/quic-go/http3"
)

//export Add
func Add(a, b int) int { return a + b }

//export Request
func Request(addr string) {
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
	defer roundTripper.Close()
	hclient := &http.Client{
		Transport: roundTripper,
	}

	fmt.Printf("GET %s\n", addr)
	rsp, err := hclient.Get(addr)
	if err != nil {
		panic(err)
	}
	fmt.Printf("GET response %s: %#v\n", addr, rsp)

	body := &bytes.Buffer{}
	_, err = io.Copy(body, rsp.Body)
	if err != nil {
		fmt.Println(err.Error())
	}
	fmt.Printf("response body: %s\n", body.Bytes())
}

func main() {}
