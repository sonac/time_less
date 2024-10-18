#!/bin/bash
# entrypoint.sh

set -e

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

exec "$@"