#!/bin/bash
set -eux

cd ../../../quic-go
git checkout master
git pull origin master
cd -

go build -o h3client.so -buildmode=c-shared h3client.go
