#!/bin/bash
set -eux

cd ../../../quic-go
git pull origin master
cd -
go build -o h2client.so -buildmode=c-shared h2client.go
go build -o h3client.so -buildmode=c-shared h3client.go
