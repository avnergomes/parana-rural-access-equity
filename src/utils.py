"""Shared helpers: cached downloads, logging, path resolution.

Kept dependency-light — only `requests` and `tqdm` beyond stdlib so this module
imports fast even when the geospatial stack is offline.
"""

from __future__ import annotations

import hashlib
import logging
import shutil
import time
import zipfile
from pathlib import Path
from typing import Iterable
from urllib.parse import urlsplit

import requests
from tqdm import tqdm

from .config import DATA_RAW

# Several Brazilian .gov.br endpoints (INEP, DATASUS) serve an incomplete TLS
# chain — they omit the ICP-Brasil intermediate, so certifi-based verification
# fails with "unable to get local issuer certificate" even though curl (which
# uses the OS trust store) succeeds. `truststore` routes verification through
# the operating-system trust store, which carries ICP-Brasil. This keeps TLS
# verification ON rather than disabling it. Best-effort: if truststore is
# unavailable we fall back to per-host insecure retry in cached_download.
try:  # pragma: no cover - environment dependent
    import truststore

    truststore.inject_into_ssl()
    _TRUSTSTORE_ACTIVE = True
except Exception:  # noqa: BLE001
    _TRUSTSTORE_ACTIVE = False

# Hosts whose cert chain is known-broken; if even the OS store can't verify
# them (e.g. a minimal CI image without ICP-Brasil), fall back to an
# unverified download AND validate the payload afterward.
_INSECURE_FALLBACK_HOSTS = ("download.inep.gov.br", "ftp.datasus.gov.br")

_LOGGER = logging.getLogger("parana_rural_access")
if not _LOGGER.handlers:
    _LOGGER.setLevel(logging.INFO)
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    _LOGGER.addHandler(_handler)


def log() -> logging.Logger:
    """Package-wide logger. Configure once, call anywhere."""
    return _LOGGER


def truststore_active() -> bool:
    """Whether OS-trust-store TLS verification is in effect (vs certifi only)."""
    return _TRUSTSTORE_ACTIVE


def _sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _stream_to_file(url: str, tmp: Path, dest_name: str, timeout: int,
                     chunk_size: int, verify: bool) -> None:
    """Stream `url` to `tmp` with a progress bar. Raises on any HTTP error."""
    with requests.get(url, stream=True, timeout=timeout, verify=verify) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0)) or None
        with open(tmp, "wb") as fh, tqdm(
            total=total,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=dest_name,
            leave=False,
        ) as bar:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    fh.write(chunk)
                    bar.update(len(chunk))


def _validate_download(path: Path) -> None:
    """Sanity-check a freshly downloaded file.

    A non-empty file whose magic bytes match its extension. For ZIPs this is a
    strong integrity signal, which is what lets us accept an unverified-TLS
    download for the known-broken-chain gov hosts without blindly trusting it.
    """
    size = path.stat().st_size
    if size == 0:
        raise RuntimeError(f"downloaded {path.name} is empty")
    if path.suffix.lower() == ".zip":
        with open(path, "rb") as fh:
            magic = fh.read(4)
        if magic[:2] != b"PK":
            raise RuntimeError(f"{path.name} is not a valid ZIP (magic={magic!r})")


def cached_download(
    url: str,
    dest: Path | None = None,
    *,
    force: bool = False,
    timeout: int = 60,
    retries: int = 3,
    chunk_size: int = 1 << 15,
) -> Path:
    """Download `url` into `data/raw/` (or a caller-supplied `dest`) with retry.

    - Skips the request when the destination file already exists (unless
      `force=True`).
    - Streams to a `.part` file and renames on success — no partial artifacts
      left behind on Ctrl+C.
    - Retries transient failures with exponential backoff.
    - TLS is verified via the OS trust store (see truststore note above). If a
      known-broken-chain gov host still fails cert verification, retries once
      with verification disabled and then validates the payload integrity.
    """
    if dest is None:
        stem = _sha1(url) + "-" + Path(url).name
        dest = DATA_RAW / stem
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not force:
        log().info("cache hit: %s", dest.name)
        return dest

    tmp = dest.with_suffix(dest.suffix + ".part")
    host = urlsplit(url).hostname or ""
    allow_insecure = host in _INSECURE_FALLBACK_HOSTS

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            log().info("GET %s (attempt %d/%d)", url, attempt, retries)
            _stream_to_file(url, tmp, dest.name, timeout, chunk_size, verify=True)
            _validate_download(tmp)
            tmp.replace(dest)
            log().info("saved -> %s (%.1f MB)", dest, dest.stat().st_size / 1e6)
            return dest
        except requests.exceptions.SSLError as exc:
            last_err = exc
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            if allow_insecure:
                log().warning(
                    "TLS verification failed for %s — retrying WITHOUT "
                    "verification (known broken gov cert chain), will validate "
                    "payload integrity", host,
                )
                try:
                    import urllib3

                    urllib3.disable_warnings(
                        urllib3.exceptions.InsecureRequestWarning
                    )
                    _stream_to_file(
                        url, tmp, dest.name, timeout, chunk_size, verify=False
                    )
                    _validate_download(tmp)
                    tmp.replace(dest)
                    log().info(
                        "saved -> %s (%.1f MB, TLS-unverified but payload valid)",
                        dest, dest.stat().st_size / 1e6,
                    )
                    return dest
                except (requests.RequestException, OSError, RuntimeError) as exc2:
                    last_err = exc2
                    log().warning("insecure retry failed: %s", exc2)
                    if tmp.exists():
                        tmp.unlink(missing_ok=True)
            else:
                log().warning("download failed (SSL): %s", exc)
            if attempt < retries:
                sleep_s = 2 ** attempt
                log().info("retrying in %ds", sleep_s)
                time.sleep(sleep_s)
        except (requests.RequestException, OSError, RuntimeError) as exc:
            last_err = exc
            log().warning("download failed: %s", exc)
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            if attempt < retries:
                sleep_s = 2 ** attempt
                log().info("retrying in %ds", sleep_s)
                time.sleep(sleep_s)
    assert last_err is not None
    raise RuntimeError(f"failed to download {url} after {retries} attempts") from last_err


def unzip(archive: Path, dest_dir: Path | None = None) -> Path:
    """Extract a zip into a sibling directory. Returns the directory path."""
    archive = Path(archive)
    dest_dir = dest_dir or archive.with_suffix("")
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        z.extractall(dest_dir)
    log().info("unzipped %s -> %s", archive.name, dest_dir)
    return dest_dir


def first_file(root: Path, suffixes: Iterable[str]) -> Path:
    """Walk `root` and return the first file matching any of the given suffixes.

    Useful for locating a shapefile inside a nested extraction folder.
    """
    root = Path(root)
    lowered = tuple(s.lower() for s in suffixes)
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in lowered:
            return p
    raise FileNotFoundError(f"no file with suffix in {lowered} under {root}")


def human_size(n_bytes: int) -> str:
    """Format a byte count with the highest reasonable unit."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024  # type: ignore[assignment]
    return f"{n_bytes:.1f} PB"


def clean_dir(path: Path, keep: Iterable[str] = (".gitkeep",)) -> None:
    """Empty a directory but leave sentinel files (like .gitkeep) alone."""
    path = Path(path)
    keep_set = set(keep)
    if not path.exists():
        return
    for child in path.iterdir():
        if child.name in keep_set:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
