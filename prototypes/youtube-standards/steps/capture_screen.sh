#!/bin/sh
# PROTOTYPE option C: live screen capture, run by the owner (never by the agent).
# Before: Focus on (Do Not Disturb), "Show notifications when mirroring or sharing" off, close private windows,
# terminal/editor font >= 20pt, pointer size enlarged (Accessibility > Display > Pointer).
# Usage: steps/capture_screen.sh <seconds> ; screen index from: ffmpeg -f avfoundation -list_devices true -i ""
SCREEN=${SCREEN:-3}
ffmpeg -f avfoundation -capture_cursor 1 -capture_mouse_clicks 1 -framerate 30 -i "${SCREEN}:none" \
  -t "${1:-20}" -vf "scale=1920:-2,format=yuv420p" -c:v libx264 -crf 20 "$(dirname "$0")/../out/capture/live.mp4"
