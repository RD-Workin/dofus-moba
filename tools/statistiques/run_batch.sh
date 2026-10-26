#!/bin/sh
# usage: run_batch.sh <tag> <worker> <n>
cd ${DIR:-$HOME/sim/godot}
i=0
while [ $i -lt $3 ]; do
  STAT_OUT=$HOME/sim/out/$1_w$2.jsonl timeout 1500 ~/godot/Godot_v4.4.1-stable_linux.x86_64 --headless --fixed-fps 20 --disable-vsync --path . -- --stattest 2>&1 | grep STATTEST >> $HOME/sim/out/$1_w$2.log
  i=$((i+1))
done
