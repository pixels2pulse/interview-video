# Interview Analysis Client Guide

Remote interview-video analysis for finance / CEO interviews.

You **upload a video** to a hosted API and **download a result zip**.  
The analysis code and models stay on the server; this repository only documents how to call the service.

## What you need

1. The service base URL (ask the service operator)
2. An API key (`X-API-Key`) issued to you
3. `curl` and `python3` (for the helper script), or any HTTP client

## Quick start

```bash
export SERVICE_URL='<SERVICE_BASE_URL>'
export API_KEY='<API_KEY>'

chmod +x examples/submit_job.sh
./examples/submit_job.sh /path/to/interview.mp4
```

When the job finishes, the script writes `result.zip` in the current directory (override with `RESULT_OUT`).

Python alternative:

```bash
export SERVICE_URL='<SERVICE_BASE_URL>'
export API_KEY='<API_KEY>'
python3 examples/submit_job.py /path/to/interview.mp4 -o result.zip
```

## API overview

All endpoints except `/health` require header:

```http
X-API-Key: <API_KEY>
```

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness check (no key) |
| `POST` | `/v1/jobs` | Upload a video (`multipart/form-data`) |
| `GET` | `/v1/jobs/{job_id}` | Job status |
| `GET` | `/v1/jobs` | Recent jobs |
| `GET` | `/v1/jobs/{job_id}/result` | Download result zip when `status=done` |

### Upload form fields

| Field | Default | Meaning |
|-------|---------|---------|
| `file` | required | Video file (`.mp4`, `.mkv`, `.mov`, `.avi`, `.webm`) |
| `include_clips` | `false` | Include cut clips in the zip (much larger) |
| `skip_visual` | `false` | Skip HRV / half-face metrics |
| `skip_emotion` | `false` | Skip audio emotion metrics |

### Job status values

`queued` → `running` → `done` or `failed` (later may become `expired`)

## Manual curl example

```bash
# 1) Upload
RESP=$(curl -sS -X POST "$SERVICE_URL/v1/jobs" \
  -H "X-API-Key: $API_KEY" \
  -F "file=@interview.mp4" \
  -F "include_clips=false")
echo "$RESP"
JOB_ID=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["job_id"])' <<<"$RESP")

# 2) Poll
curl -sS -H "X-API-Key: $API_KEY" "$SERVICE_URL/v1/jobs/$JOB_ID"

# 3) Download when status is done
curl -sS -H "X-API-Key: $API_KEY" \
  -o result.zip "$SERVICE_URL/v1/jobs/$JOB_ID/result"
```

## What is inside the result zip

| Path | Contents |
|------|----------|
| `results/pipeline_summary.json` | Run summary |
| `results/qa_pairs.csv` | Question–answer pairs and timestamps |
| `results/pressure_scores.csv` | Journalist-question pressure scores |
| `results/answer_attitude.csv` | CEO answer attitude labels |
| `results/audio_emotion.csv` | Arousal / Dominance / Valence and window stats |
| `results/audio_emotion_windows/` | Per-window emotion JSON |
| `results/resilience.csv` | HRV / recovery proxies |
| `results/face_asymmetry.csv` | Half-face asymmetry metrics |
| `results/labeled_transcripts/` | Role-labeled turns / pairs |
| `clips/` | Only if `include_clips=true` |

## Notes

- One GPU processes **one job at a time**; your upload may wait in a queue.
- Prefer shorter clips when testing; large files take longer and use more disk on the server.
- Keep your API key private. Do not commit real keys to git.
- Copy `env.example` to `.env` locally if you want a template for URL/key (do not commit `.env`).

Full field-level notes: [docs/API.md](docs/API.md).

## Repository scope

This public repo contains **client documentation and helper scripts only**.  
It does **not** include the analysis source code, models, or server deployment files.

## Video Demo



https://github.com/user-attachments/assets/073dbd2f-e981-45bb-8c51-aaf986be6202


