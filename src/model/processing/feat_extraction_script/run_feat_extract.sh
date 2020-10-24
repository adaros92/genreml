#!/bin/bash
FOLDER_START=91
FOLDER_END=100
for (( i=${FOLDER_START}; i<=${FOLDER_END}; i++)) 
do
    python3 extract_data.py $i 
done