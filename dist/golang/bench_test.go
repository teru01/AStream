package main

import "testing"

func BenchmarkH3client(b *testing.B) {
	url := "https://dash.localdomain:6666/fall.jpg"
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		h3client(url)
	}

	// select {
	// case <-quit:
		
	// }
}


func BenchmarkH2client(b *testing.B) {
	url := "https://dash.localdomain:4443/fall.jpg"
	b.ResetTimer()
	for i:=0; i<b.N; i++ {
		h2client(url)
	}
}
