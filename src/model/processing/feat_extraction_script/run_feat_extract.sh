#!/bin/bash
FOLDER_START=141
FOLDER_END=155
for (( i=${FOLDER_START}; i<=${FOLDER_END}; i++)) 
do
    python3 extract_data.py $i 
done