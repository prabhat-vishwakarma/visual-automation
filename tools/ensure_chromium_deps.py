"""No-root fix-up for Playwright Chromium shared libraries.

On systems where `playwright install-deps` needs root (shared/WSL boxes,
non-root CI runners), Chromium may fail to launch with messages like
`libnss3.so => not found`.

This script:
    1. finds the Playwright-installed browser binaries,
    2. checks `ldd` for missing shared libraries,
    3. if only NSS/NSPR libraries are missing, downloads the matching .deb
       packages with `apt-get download` (no root required) and extracts them
       into a project-local directory,
    4. prints the LD_LIBRARY_PATH to use (or exports it for a child command).

Usage:
    python -m tools.ensure_chromium_deps
    python -m tools.ensure_chromium_deps --command \\
        ".venv/bin/python -m app.main --config config/local-test.yaml"
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEPS_DIR = REPO_ROOT / ".chromium-deps"
MISSING_NAME_MAP = {
    "libnss3.so": "libnss3",
    "libnspr4.so": "libnspr4",
    "libnssutil3.so": "libnss3",
    "libssl3.so": "libnss3",
    "libsmime3.so": "libnss3",
    "libsoftokn3.so": "libnss3",
}


def find_browser_binaries() -> list[Path]:
    cache = Path(
        os.environ.get(
            "PLAYWRIGHT_BROWSERS_PATH",
            str(Path.home() / ".cache" / "ms-playwright"),
        )
    )
    shell_glob = (
        "chromium_headless_shell-*/"
        "chrome-headless-shell-linux64/chrome-headless-shell"
    )
    binaries = [
        *glob.glob(str(cache / shell_glob)),
        *glob.glob(str(cache / "chromium-*/chrome-linux/chrome")),
    ]
    return [Path(p) for p in binaries if Path(p).exists()]


def missing_libraries(binary: Path) -> list[str]:
    result = subprocess.run(
        ["ldd", str(binary)],
        capture_output=True,
        text=True,
        check=False,
    )
    missing: list[str] = []
    for line in result.stdout.splitlines():
        if "not found" in line:
            lib = line.split("=>")[0].strip()
            missing.append(lib)
    return missing


def download_and_extract(packages: set[str]) -> Path:
    debs_dir = DEPS_DIR / "debs"
    extracted_dir = DEPS_DIR / "extracted"
    ubuntu_lib = extracted_dir / "usr" / "lib" / "x86_64-linux-gnu"
    if ubuntu_lib.is_dir() and any(ubuntu_lib.glob("*.so*")):
        return ubuntu_lib

    extracted_dir.mkdir(parents=True, exist_ok=True)
    for package in sorted(packages):
        subprocess.run(
            ["apt-get", "download", package],
            cwd=str(debs_dir),
            check=True,
        )
        debs = sorted(debs_dir.glob(f"{package}_*.deb"))
        if not debs:
            raise RuntimeError(f"no .deb downloaded for {package}")
        subprocess.run(
            ["dpkg-deb", "-x", str(debs[-1]), str(extracted_dir)],
            check=True,
        )
    return ubuntu_lib


def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--command",
        help="run this shell command after exporting LD_LIBRARY_PATH",
    )
    args = parser.parse_args()

    binaries = find_browser_binaries()
    if not binaries:
        print("No Playwright Chromium binaries found. Run 'playwright install chromium' first.")
        return 2

    needed_packages: set[str] = set()
    for binary in binaries:
        for lib in missing_libraries(binary):
            package = MISSING_NAME_MAP.get(lib)
            print(f"{binary.name}: missing {lib}")
            if package:
                needed_packages.add(package)
            else:
                print(
                    f"  -> {lib} is missing. Install OS dependencies with root: "
                    "'playwright install-deps chromium'."
                )
                return 3

    if not needed_packages:
        print("All Chromium shared libraries present.")
        return 0

    try:
        lib_dir = download_and_extract(needed_packages)
    except Exception as exc:
        print(f"Failed to download/extract debs: {exc}")
        return 4

    library_path = os.environ.get("LD_LIBRARY_PATH", "")
    combined = f"{lib_dir}{os.pathsep + library_path if library_path else ''}"

    if args.command:
        env = dict(os.environ)
        env["LD_LIBRARY_PATH"] = combined
        return subprocess.run(
            ["bash", "-c", args.command], env=env, check=False
        ).returncode

    print(f"Export LD_LIBRARY_PATH for Chromium:\n  export LD_LIBRARY_PATH=\"{combined}\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())