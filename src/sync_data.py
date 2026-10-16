"""Sync heavy local data with the private S3 bucket (too big for git).

    python src/sync_data.py status raw         # local vs S3 listing
    python src/sync_data.py push raw           # upload data/raw/*.7z + SHA-256 manifest
    python src/sync_data.py pull raw           # download and verify against the manifest
    python src/sync_data.py push embeddings    # data/embeddings/embeddings.duckdb (close writers first)

Credentials come from .secrets/aws_access_key.txt and .secrets/aws_secret_key.txt (gitignored),
or from the normal AWS environment/profile if those files are absent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUCKET = "s3://biddy-homogenization"
REGION = "us-west-2"
TARGETS = {"raw": (ROOT / "data" / "raw", "*.7z"),
           "embeddings": (ROOT / "data" / "embeddings", "embeddings.duckdb")}
MANIFEST = "MANIFEST.json"


def aws_env() -> dict[str, str]:
    env = dict(os.environ, AWS_DEFAULT_REGION=REGION)
    key, secret = ROOT / ".secrets" / "aws_access_key.txt", ROOT / ".secrets" / "aws_secret_key.txt"
    if key.exists() and secret.exists():
        env.update(AWS_ACCESS_KEY_ID=key.read_text().strip(), AWS_SECRET_ACCESS_KEY=secret.read_text().strip())
        env.pop("AWS_PROFILE", None)
        env.pop("AWS_SESSION_TOKEN", None)
    return env


def aws(*args: str, capture: bool = False) -> str:
    res = subprocess.run(["aws", *args], env=aws_env(), check=True, text=True,
                         capture_output=capture)
    return res.stdout if capture else ""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def remote_listing(name: str) -> dict[str, int]:
    out = aws("s3api", "list-objects-v2", "--bucket", BUCKET[5:], "--prefix", f"{name}/",
              "--output", "json", capture=True)
    return {Path(o["Key"]).name: o["Size"] for o in json.loads(out or "{}").get("Contents", [])}


def push(name: str) -> None:
    folder, pattern = TARGETS[name]
    files = sorted(folder.glob(pattern))
    manifest = {f.name: {"size": f.stat().st_size, "sha256": sha256(f)} for f in files}
    aws("s3", "sync", str(folder), f"{BUCKET}/{name}/", "--exclude", "*", "--include", pattern,
        "--no-progress")
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tmp:
        json.dump(manifest, tmp, indent=1)
    aws("s3", "cp", tmp.name, f"{BUCKET}/{name}/{MANIFEST}", "--no-progress")
    os.unlink(tmp.name)
    remote = remote_listing(name)
    bad = [n for n, m in manifest.items() if remote.get(n) != m["size"]]
    if bad:
        sys.exit(f"size mismatch after upload: {bad}")
    print(f"pushed {len(manifest)} files, {sum(m['size'] for m in manifest.values()) / 2**30:.2f} GiB; sizes verified")


def pull(name: str) -> None:
    folder, pattern = TARGETS[name]
    folder.mkdir(parents=True, exist_ok=True)
    aws("s3", "sync", f"{BUCKET}/{name}/", str(folder), "--exclude", MANIFEST, "--no-progress")
    manifest = json.loads(aws("s3", "cp", f"{BUCKET}/{name}/{MANIFEST}", "-", capture=True))
    bad = [n for n, m in manifest.items() if not (folder / n).exists() or sha256(folder / n) != m["sha256"]]
    if bad:
        sys.exit(f"checksum mismatch: {bad}")
    print(f"pulled and verified {len(manifest)} files")


def status(name: str) -> None:
    folder, pattern = TARGETS[name]
    local = {f.name: f.stat().st_size for f in folder.glob(pattern)}
    remote = {k: v for k, v in remote_listing(name).items() if k != MANIFEST}
    for n in sorted(local.keys() | remote.keys()):
        where = "both" if local.get(n) == remote.get(n) else "local" if n not in remote else "s3" if n not in local else "DIFF"
        print(f"{where:5}  {n}")
    print(f"local {len(local)} files, s3 {len(remote)} files")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["push", "pull", "status"])
    ap.add_argument("target", choices=sorted(TARGETS))
    args = ap.parse_args()
    {"push": push, "pull": pull, "status": status}[args.action](args.target)


if __name__ == "__main__":
    main()
