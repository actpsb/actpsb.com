"""Build the three File Manager upload ZIPs into dist/ (git-ignored). Standard library only.

  actpsb-public.zip   -> extract into /home/arriscom/public_html/actpsb.com
  actpsb-backend.zip  -> extract into /home/arriscom/actpsb-backend (vendor/ included, no Composer on server)
  actpsb-private.zip  -> extract into /home/arriscom/actpsb-private (placeholder config.php, no secrets)

Needs php and composer on the BUILD machine only: set ACTP_PHP and ACTP_COMPOSER (path to composer.phar)
if they are not on PATH. Nothing here talks to a server.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_FILES = ["index.html", "about.html", "services.html", "nsx-adviser.html", "insights.html",
                "contact.html", "robots.txt", "contact-submit.php"]
PUBLIC_DIRS = ["assets"]
FIXED_TIME = (2026, 1, 1, 0, 0, 0)


def add(z: zipfile.ZipFile, path: Path, arc: str):
    info = zipfile.ZipInfo(arc, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (0o644 if path.is_file() else 0o755) << 16
    z.writestr(info, path.read_bytes())


def zip_tree(out: Path, base: Path, files):
    with zipfile.ZipFile(out, "w") as z:
        for f in sorted(files):
            add(z, f, f.relative_to(base).as_posix())


def build(dist: Path) -> dict:
    php = os.environ.get("ACTP_PHP") or shutil.which("php")
    composer = os.environ.get("ACTP_COMPOSER") or shutil.which("composer")
    if not php or not composer:
        raise SystemExit("php and composer (or ACTP_PHP / ACTP_COMPOSER) are required on the build machine")
    cmd = [php, composer] if composer.endswith(".phar") else [composer]
    shutil.rmtree(dist, ignore_errors=True)
    dist.mkdir(parents=True)

    with tempfile.TemporaryDirectory() as t:
        stage = Path(t) / "backend"
        stage.mkdir()
        for name in ("composer.json", "composer.lock"):
            shutil.copy(ROOT / "backend" / name, stage / name)
        shutil.copytree(ROOT / "backend/src", stage / "src")
        shutil.copytree(ROOT / "backend/licenses", stage / "licenses")
        subprocess.run([*cmd, "install", "--no-dev", "--optimize-autoloader", "--no-interaction",
                        "--no-progress", "--working-dir", str(stage)], check=True, capture_output=True)
        zip_tree(dist / "actpsb-backend.zip", stage, [p for p in stage.rglob("*") if p.is_file()])

    pub = [ROOT / f for f in PUBLIC_FILES]
    for d in PUBLIC_DIRS:
        pub += [p for p in (ROOT / d).rglob("*") if p.is_file()]
    zip_tree(dist / "actpsb-public.zip", ROOT, pub)

    cfg = (ROOT / "backend/config/config.example.php").read_text(encoding="utf-8")
    with zipfile.ZipFile(dist / "actpsb-private.zip", "w") as z:
        info = zipfile.ZipInfo("config.php", FIXED_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o600 << 16
        z.writestr(info, cfg)
    return {p.name: p.stat().st_size for p in sorted(dist.glob("*.zip"))}


if __name__ == "__main__":
    for name, size in build(ROOT / "dist").items():
        print(f"{name}  {size} bytes")
    sys.exit(0)
