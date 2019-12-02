package main

import "testing"


func BenchmarkH2client(b *testing.B) {
	url := "https://dash.localdomain:4443/fall.jpg"
	for i:=0; i<b.N; i++ {
		h2client(url)
	}
}
