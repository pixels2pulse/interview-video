#!/usr/bin/env python3
"""Upload a video to the hosted analysis API, wait, and download the result zip.

Requires only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _request(
    method: str,
    url: str,
    *,
    api_key: str,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    hdrs = {"X-API-Key": api_key}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            return resp.status, resp.read(), dict(resp.headers.items())
    except urllib.error.HTTPError as exc:
        body = exc.read()
        raise SystemExit(f"HTTP {exc.code}: {body.decode('utf-8', errors='replace')}") from exc


def _multipart(field_name: str, filename: str, content: bytes, fields: dict[str, str]) -> tuple[bytes, str]:
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode())
        chunks.append(f"{value}\r\n".encode())
    chunks.append(f"--{boundary}\r\n".encode())
    chunks.append(
        (
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
    )
    chunks.append(content)
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    body = b"".join(chunks)
    return body, f"multipart/form-data; boundary={boundary}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Submit a video to the hosted analysis service")
    parser.add_argument("video", type=Path, help="Path to the interview video")
    parser.add_argument("-o", "--output", type=Path, default=Path("result.zip"))
    parser.add_argument("--include-clips", action="store_true")
    parser.add_argument("--skip-visual", action="store_true")
    parser.add_argument("--skip-emotion", action="store_true")
    parser.add_argument("--poll-sec", type=float, default=10.0)
    args = parser.parse_args()

    base = (os.environ.get("SERVICE_URL") or "").rstrip("/")
    key = os.environ.get("API_KEY") or ""
    if not base or not key:
        raise SystemExit("Set SERVICE_URL and API_KEY in the environment")
    if not args.video.is_file():
        raise SystemExit(f"Video not found: {args.video}")

    content = args.video.read_bytes()
    body, content_type = _multipart(
        "file",
        args.video.name,
        content,
        {
            "include_clips": "true" if args.include_clips else "false",
            "skip_visual": "true" if args.skip_visual else "false",
            "skip_emotion": "true" if args.skip_emotion else "false",
        },
    )
    status, raw, _ = _request(
        "POST",
        f"{base}/v1/jobs",
        api_key=key,
        data=body,
        headers={"Content-Type": content_type},
    )
    payload = json.loads(raw.decode("utf-8"))
    job_id = payload["job_id"]
    print(f"job_id={job_id} http={status}")

    while True:
        _, raw, _ = _request("GET", f"{base}/v1/jobs/{job_id}", api_key=key)
        info = json.loads(raw.decode("utf-8"))
        st = info["status"]
        print(f"status={st}")
        if st == "done":
            _, zip_bytes, _ = _request("GET", f"{base}/v1/jobs/{job_id}/result", api_key=key)
            args.output.write_bytes(zip_bytes)
            print(f"saved {args.output}")
            return
        if st in {"failed", "expired"}:
            print(json.dumps(info, ensure_ascii=False, indent=2), file=sys.stderr)
            raise SystemExit(1)
        time.sleep(args.poll_sec)


if __name__ == "__main__":
    main()
