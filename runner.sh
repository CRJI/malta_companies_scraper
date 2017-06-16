#!/usr/bin/env bash

python3 gather.py;

mkdir output;

while [ $? -ne 0 ]; do
    python3 lookup.py;
done;
