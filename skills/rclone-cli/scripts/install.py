#!/usr/bin/env python3
"""Install a local rclone release ZIP without downloading or running its contents."""

import argparse
import hashlib
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import sys
import tempfile
import zipfile


def release_platform():
    systems = {
        "Linux": "linux", "Darwin": "osx", "FreeBSD": "freebsd",
        "OpenBSD": "openbsd", "NetBSD": "netbsd",
    }
    system = systems.get(platform.system())
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        arch = "amd64"
    elif machine in ("aarch64", "arm64"):
        arch = "arm64"
    elif re.fullmatch(r"i[3-6]86|x86", machine):
        arch = "386"
    elif machine.startswith("armv7"):
        arch = "arm-v7"
    elif machine.startswith("armv6"):
        arch = "arm-v6"
    elif machine.startswith("arm"):
        arch = "arm"
    else:
        raise ValueError("Unsupported CPU architecture; use the official manual instructions.")
    if system is None:
        raise ValueError("Unsupported OS; use the official manual instructions.")
    return system, arch


def install(archive, version, expected_sha256, bin_dir):
    """Verify a private snapshot, extract one binary, and replace the user destination."""
    if not hasattr(os, "geteuid") or os.geteuid() == 0:
        raise ValueError("Run as a regular user, without sudo or a root shell.")
    if not re.fullmatch(r"v?[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("Version must name a stable release, such as 1.70.3; latest/beta are not accepted.")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256):
        raise ValueError("Supply a SHA-256 digest from an independently verified release manifest.")
    if not bin_dir.is_absolute():
        raise ValueError("The binary directory must be an absolute path.")
    system, arch = release_platform()
    member_name = "rclone-v{}-{}-{}/rclone".format(version.lstrip("v"), system, arch)
    destination = bin_dir / "rclone"

    with tempfile.TemporaryDirectory(prefix="rclone-install-") as workspace:
        # Hash and extract the same private copy, even if the source later changes.
        snapshot = Path(workspace) / "release.zip"
        digest = hashlib.sha256()
        with archive.open("rb") as source, snapshot.open("wb") as target:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
                target.write(chunk)
        if digest.hexdigest() != expected_sha256.lower():
            raise ValueError("SHA-256 mismatch; nothing was installed.")

        staged = Path(workspace) / "rclone"
        with zipfile.ZipFile(snapshot) as release:
            members = [info for info in release.infolist() if info.filename == member_name]
            if len(members) != 1:
                raise ValueError("Archive must contain exactly one binary for the requested version and platform.")
            member = members[0]
            file_type = stat.S_IFMT(member.external_attr >> 16)
            if file_type not in (0, stat.S_IFREG) or member.file_size == 0:
                raise ValueError("The release binary must be a nonempty regular file.")
            # Never extract archive paths, symlinks, scripts, or ancillary files.
            with release.open(member) as source, staged.open("wb") as target:
                shutil.copyfileobj(source, target)

        if destination.is_symlink() or (destination.exists() and not destination.is_file()):
            raise ValueError("Refusing to replace a symlink or non-file destination.")
        bin_dir.mkdir(parents=True, exist_ok=True)
        descriptor, pending_name = tempfile.mkstemp(prefix=".rclone-install-", dir=str(bin_dir))
        pending = Path(pending_name)
        try:
            with os.fdopen(descriptor, "wb") as target, staged.open("rb") as source:
                shutil.copyfileobj(source, target)
                os.fchmod(target.fileno(), 0o755)
            os.replace(str(pending), str(destination))
        finally:
            pending.unlink(missing_ok=True)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="Local official release ZIP")
    parser.add_argument("--version", required=True, help="Exact stable release, e.g. 1.70.3")
    parser.add_argument("--sha256", required=True, help="Expected digest from a verified release manifest")
    parser.add_argument("--bin-dir", type=Path, default=Path.home() / ".local" / "bin")
    args = parser.parse_args()
    try:
        destination = install(args.archive, args.version, args.sha256, args.bin_dir.expanduser())
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        print("Installation failed: {}".format(error), file=sys.stderr)
        return 1
    print("Installed rclone {} to {}. No binary was executed.".format(args.version, destination))
    return 0


if __name__ == "__main__":
    sys.exit(main())
