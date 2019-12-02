package main

import "testing"

func Benchmarkh3client(b *testing.B) {
	url := "https://dash.localdomain:6666/fall.jpg"
	for i := 0; i < b.N; i++ {
		h3client(url)
	}
}
