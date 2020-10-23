#!/bin/bash
FOLDER_START=46
FOLDER_END=50
for (( i=${FOLDER_START}; i<=${FOLDER_END}; i++)) 
do
    python3 extract_data.py $i 
done