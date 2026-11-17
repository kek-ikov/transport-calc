#!/bin/sh
awk '/MemTotal:/ {t=$2} /MemAvailable:/ {a=$2} END {printf "Available: %.2f GiB (%.1f%%); used: %.1f%%\n",a/1048576,100*a/t,100*(t-a)/t; exit (a/t < 0.15)}' /proc/meminfo
