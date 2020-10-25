#!/bin/bash
FOLDER_START=31
FOLDER_END=40
for (( i=${FOLDER_START}; i<=${FOLDER_END}; i++)) 
do
    python3 extract_spect.py $i 
done