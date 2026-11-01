#!/usr/bin/env bash
# Upload a video, wait until the job finishes, download the result zip.
#
#   export SERVICE_URL='<SERVICE_BASE_URL>'
#   export API_KEY='<API_KEY>'
#   ./examples/submit_job.sh /path/to/video.mp4
set -euo pipefail

VIDEO="${1:-}"
if [[ -z "$VIDEO" || ! -f "$VIDEO" ]]; then
  echo "Usage: $0 /path/to/video.mp4" >&2
  exit 2
fi

URL="${SERVICE_URL:?set SERVICE_URL to the service base URL}"
KEY="${API_KEY:?set API_KEY}"
INCLUDE_CLIPS="${INCLUDE_CLIPS:-false}"
SKIP_VISUAL="${SKIP_VISUAL:-false}"
SKIP_EMOTION="${SKIP_EMOTION:-false}"
OUT="${RESULT_OUT:-./result.zip}"

RESP="$(curl -sS -X POST "$URL/v1/jobs" \
  -H "X-API-Key: $KEY" \
  -F "file=@${VIDEO}" \
  -F "include_clips=${INCLUDE_CLIPS}" \
  -F "skip_visual=${SKIP_VISUAL}" \
  -F "skip_emotion=${SKIP_EMOTION}")"

if ! JOB_ID="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["job_id"])' <<<"$RESP" 2>/dev/null)"; then
  echo "Upload failed or response was not JSON:" >&2
  echo "$RESP" >&2
  exit 1
fi
echo "job_id=$JOB_ID"

while true; do
  STATUS_JSON="$(curl -sS -H "X-API-Key: $KEY" "$URL/v1/jobs/$JOB_ID")"
  STATUS="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])' <<<"$STATUS_JSON")"
  echo "status=$STATUS"
  case "$STATUS" in
    done)
      curl -sS -H "X-API-Key: $KEY" -o "$OUT" "$URL/v1/jobs/$JOB_ID/result"
      echo "saved $OUT"
      exit 0
      ;;
    failed|expired)
      echo "$STATUS_JSON" >&2
      exit 1
      ;;
  esac
  sleep 10
done
