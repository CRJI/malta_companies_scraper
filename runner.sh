#!/usr/bin/env bash

python3 gather.py;

while [ $? -ne 0 ]; do
    python3 lookup.py;
done;
