# API reference

Base URL is provided by the service operator. Authenticate with:

```http
X-API-Key: <key>
```

Unless noted, responses are JSON.

## `GET /health`

No authentication.

Example response:

```json
{"status": "ok", "service": "interview-analysis", "version": "0.1.0"}
```

## `POST /v1/jobs`

Upload one video and enqueue analysis.

`Content-Type: multipart/form-data`

| Part | Type | Required | Description |
|------|------|----------|-------------|
| `file` | file | yes | Interview video |
| `include_clips` | string bool | no | `true` / `false` |
| `skip_visual` | string bool | no | `true` / `false` |
| `skip_emotion` | string bool | no | `true` / `false` |

Success `200`:

```json
{
  "job_id": "a1b2c3...",
  "status": "queued",
  "message": "Job accepted. Poll GET /v1/jobs/{job_id}; download GET /v1/jobs/{job_id}/result when done."
}
```

Common errors:

- `401` invalid or missing API key
- `400` unsupported type or empty upload
- `413` file larger than the server limit

## `GET /v1/jobs/{job_id}`

Success `200`:

```json
{
  "job_id": "a1b2c3...",
  "status": "running",
  "original_filename": "interview.mp4",
  "created_at": "2026-11-01T18:00:00+00:00",
  "updated_at": "2026-11-01T18:01:00+00:00",
  "started_at": "2026-11-01T18:00:30+00:00",
  "finished_at": null,
  "include_clips": false,
  "skip_visual": false,
  "skip_emotion": false,
  "error": null,
  "result_ready": false
}
```

When `status` is `failed`, read `error` for a short message.  
When `status` is `done`, `result_ready` is `true`.

## `GET /v1/jobs`

List recent jobs (newest first). Query: `limit` (1–200, default 50).

## `GET /v1/jobs/{job_id}/result`

Returns a zip file when the job is `done`.

- `200` with `Content-Type: application/zip`
- `409` if the job is not finished yet
- `404` if the job or zip is missing / expired

## Status lifecycle

```
queued → running → done
                 ↘ failed
done|failed → expired   (after the server retention window)
```
