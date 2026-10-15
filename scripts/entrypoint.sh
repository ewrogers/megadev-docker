#!/bin/sh
set -eu
if [ "$#" -eq 0 ]; then set -- build; fi
case "$1" in
    build) shift; exec make "$@" ;;
    doctor) shift; exec /usr/local/bin/megadev-doctor "$@" ;;
    init|cue) exec /usr/local/bin/megadev-project "$@" ;;
    *) exec "$@" ;;
esac
