"""Build the three File Manager upload ZIPs into dist/ (git-ignored). Standard library only.

  actpsb-public.zip   -> extract into /home/arriscom/public_html/actpsb.com
  actpsb-backend.zip  -> extract into /home/arriscom/actpsb-backend (vendor/ included, no Composer on server)
  actpsb-private.zip  -> extract into /home/arriscom/actpsb-private (config.example.php TEMPLATE ONLY, no secrets;
                          it never contains config.php, so extracting cannot overwrite a live configuration)

Needs php and composer on the BUILD machine only: set ACTP_PHP and ACTP_COMPOSER (path to composer.phar)
if they are not on PATH. Nothing here talks to a server.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_FILES = ["index.html", "about.html", "services.html", "insights.html",
                "contact.html", "robots.txt", "favicon.ico", "contact-submit.php"]
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
        info = zipfile.ZipInfo("config.example.php", FIXED_TIME)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o600 << 16
        z.writestr(info, cfg)
    check_public_references(pub)
    write_manifest(dist)
    return {p.name: p.stat().st_size for p in sorted(dist.glob("*.zip"))}


def check_public_references(pub):
    """Fail the build if a page references a local file the public ZIP would not contain."""
    shipped = {p.relative_to(ROOT).as_posix() for p in pub}
    missing = []
    for page in ROOT.glob("*.html"):
        for ref in re.findall(r'(?:href|src)="([^"#?:]+)"', page.read_text(encoding="utf-8")):
            if ref.startswith(("http", "//", "mailto", "tel")) or ref == "":
                continue
            if ref not in shipped:
                missing.append(f"{page.name} -> {ref}")
    if missing:
        raise SystemExit("public package is missing referenced files: " + ", ".join(sorted(set(missing))))


def source_sha() -> str:
    sha = os.environ.get("GITHUB_SHA")
    if sha:
        return sha
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() or "unknown"


def write_manifest(dist: Path):
    """MANIFEST.json and SHA256SUMS.txt describe the ZIPs; they are not inside the ZIPs."""
    lock = json.loads((ROOT / "backend/composer.lock").read_text(encoding="utf-8"))
    deps = {p["name"]: p["version"] for p in lock["packages"]}
    targets = {"actpsb-public.zip": "/home/arriscom/public_html/actpsb.com",
               "actpsb-backend.zip": "/home/arriscom/actpsb-backend",
               "actpsb-private.zip": "/home/arriscom/actpsb-private"}
    zips = {}
    for name, target in targets.items():
        data = (dist / name).read_bytes()
        with zipfile.ZipFile(dist / name) as z:
            members = sorted(z.namelist())
        zips[name] = {"extract_into": target, "sha256": hashlib.sha256(data).hexdigest(),
                      "bytes": len(data), "entries": len(members), "members": members}
    manifest = {"source_sha": source_sha(), "dependencies": deps, "packages": zips}
    (dist / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (dist / "SHA256SUMS.txt").write_text(
        "".join(f"{v['sha256']}  {k}\n" for k, v in zips.items()), encoding="utf-8")


if __name__ == "__main__":
    for name, size in build(ROOT / "dist").items():
        print(f"{name}  {size} bytes")
