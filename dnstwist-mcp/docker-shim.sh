#!/bin/sh
# Docker shim for the dnstwist-mcp farm container.
#
# The upstream Node package (@burtthecoder/mcp-dnstwist) shells out to
# `docker run elceef/dnstwist …` to execute dnstwist. Farm MCP containers have no
# Docker daemon, so this shim forwards those calls to a natively-installed
# `dnstwist` binary instead. Non-run calls (version / image inspect) are answered
# so the upstream's pre-flight checks pass.
echo "[docker-shim] $*" >&2
case "$1" in
  --version|version)
    echo "Docker version 24.0.0, build farmshim"
    exit 0
    ;;
  image|images|inspect|pull)
    # Pretend the image exists / pull succeeded.
    exit 0
    ;;
  run)
    shift
    # Drop docker-run options and the image reference; forward the remaining
    # tokens (dnstwist's own arguments) to the native binary.
    while [ $# -gt 0 ]; do
      case "$1" in
        *dnstwist*) shift; break ;;
        *) shift ;;
      esac
    done
    exec dnstwist "$@"
    ;;
  *)
    exit 0
    ;;
esac
