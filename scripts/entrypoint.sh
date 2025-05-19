#!/bin/sh

if [[ -n "${OBOT_KUBERNETES_MODE}" ]]; then
    supergateway --stdio "$1" --port 8080 --healthEndpoint /healthz
fi

$1