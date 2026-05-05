#!/bin/sh
# Wrapper to run the UnixBench suite from its installation directory.
cd /opt/unix-bench && exec ./Run "$@"
