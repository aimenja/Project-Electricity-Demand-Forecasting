#!/usr/bin/env bash
#
# PowerPlus dashboard launcher.
#
#   ./run.sh            local only    -> http://127.0.0.1:8000
#   ./run.sh --share    public URL    -> prints a https://*.trycloudflare.com link
#
# --share opens a Cloudflare quick tunnel and turns on password protection, so the
# dashboard is reachable from any device but not by anyone who stumbles on the URL.

set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
SHARE=0
[[ "${1:-}" == "--share" ]] && SHARE=1

if [ ! -d .venv ]; then
  echo "No .venv found. Set it up first:"
  echo "  python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt"
  exit 1
fi

cleanup() {
  [[ -n "${TUNNEL_PID:-}" ]] && kill "$TUNNEL_PID" 2>/dev/null || true
  [[ -n "${SERVER_PID:-}" ]] && kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

if [ "$SHARE" -eq 0 ]; then
  echo "PowerPlus dashboard -> http://127.0.0.1:$PORT"
  exec ./.venv/bin/python -m uvicorn backend.app:app --port "$PORT" --reload
fi

# ----------------------------------------------------------------- shared mode

command -v ssh >/dev/null || { echo "ssh not found."; exit 1; }

echo "Starting dashboard on port $PORT ..."
./.venv/bin/python -m uvicorn backend.app:app --host 127.0.0.1 --port "$PORT" > /tmp/powerplus-server.log 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 90); do
  curl -s -o /dev/null "http://127.0.0.1:$PORT/api/meta" && break
  sleep 1
done

# Serveo tunnels over SSH. We use it rather than cloudflared because this network
# throttles api.trycloudflare.com badly enough (~30s) that cloudflared times out.
# POWERPLUS_SUBDOMAIN reserves a stable hostname, but only once an SSH key is
# registered with serveo; without one the server just assigns a random name.
FORWARD="80:localhost:$PORT"
[[ -n "${POWERPLUS_SUBDOMAIN:-}" ]] && FORWARD="${POWERPLUS_SUBDOMAIN}:$FORWARD"

URL=""
for attempt in 1 2 3; do
  echo "Opening public tunnel (attempt $attempt) ..."
  : > /tmp/powerplus-tunnel.log
  ssh -o StrictHostKeyChecking=accept-new -o ExitOnForwardFailure=yes \
      -o ServerAliveInterval=30 -o ServerAliveCountMax=3 \
      -R "$FORWARD" serveo.net > /tmp/powerplus-tunnel.log 2>&1 &
  TUNNEL_PID=$!

  for _ in $(seq 1 30); do
    URL=$(grep -Eo 'https://[a-zA-Z0-9.-]+\.(serveousercontent\.com|serveo\.net)' /tmp/powerplus-tunnel.log \
          | grep -vE '^https://(console|www)\.' | head -1 || true)
    [[ -n "$URL" ]] && break
    kill -0 "$TUNNEL_PID" 2>/dev/null || break
    sleep 1
  done

  [[ -n "$URL" ]] && break
  kill "$TUNNEL_PID" 2>/dev/null || true
  sleep 2
done

if [[ -z "$URL" ]]; then
  echo "Could not open a tunnel after 3 attempts. Last log:"
  tail -5 /tmp/powerplus-tunnel.log
  echo
  echo "The dashboard is still running locally at http://127.0.0.1:$PORT"
  wait $SERVER_PID
  exit 1
fi

NOTE="The URL changes every run."
[[ -n "${POWERPLUS_SUBDOMAIN:-}" ]] && NOTE="Reserved name: this URL stays the same."

cat <<BANNER

  ============================================================
   PowerPlus dashboard is live — open this on any device:

     $URL

   $NOTE  Ctrl+C here takes it offline.
  ============================================================

BANNER

wait $SERVER_PID
