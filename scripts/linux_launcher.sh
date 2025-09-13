#!/bin/bash
# Launch resumecli with the proper environment
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$DIR/runtime_wrapper.sh" "$@"
