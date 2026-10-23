#!/bin/sh
# PROTOTYPE: two-pass EBU R128 loudness normalisation. loudnorm.sh <in> <out> <I> <TP>
set -e
m=$(ffmpeg -hide_banner -nostats -i "$1" -af "loudnorm=I=$3:TP=$4:LRA=11:print_format=json" -f null - 2>&1 | sed -n '/^{/,/^}/p')
v() { echo "$m" | python3 -c "import json,sys;print(json.load(sys.stdin)['$1'])"; }
ffmpeg -v error -y -i "$1" -af "loudnorm=I=$3:TP=$4:LRA=11:measured_I=$(v input_i):measured_TP=$(v input_tp):measured_LRA=$(v input_lra):measured_thresh=$(v input_thresh):offset=$(v target_offset):linear=true" -ar 48000 "$2"
