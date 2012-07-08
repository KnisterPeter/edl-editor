#!/bin/sh

IN=$1
EDL=$(basename "$1" ".mkv")
EDL=$(dirname "$IN")/$EDL.edl
OUT=/tmp/$(basename "$1")

if [ -f "$IN" -a -f "$EDL" ] ; then
  mkvedlmerge -i "$IN" -o "$OUT" && mv "$OUT" "$IN" && rm "$EDL"
fi

