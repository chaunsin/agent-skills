"""Offline security regressions for the verified local-archive installer."""

import hashlib
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

import install as installer


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="test-rclone-install-")
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.archive = self.root / "release with spaces.zip"
        self.bin_dir = self.root / "user bin"
        self.member = "rclone-v1.70.3-linux-amd64/rclone"
        self.marker = self.root / "executed"
        self.binary = '#!/bin/sh\ntouch "{}"\n'.format(self.marker).encode()
        for attribute, result in (("system", "Linux"), ("machine", "x86_64")):
            mock = patch.object(installer.platform, attribute, return_value=result)
            mock.start()
            self.addCleanup(mock.stop)
        mock = patch.object(installer.os, "geteuid", return_value=1000, create=True)
        mock.start()
        self.addCleanup(mock.stop)

    def make_archive(self, entries=None):
        if entries is None:
            entries = [(self.member, self.binary)]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.archive, "w") as release:
                for name, data in entries:
                    release.writestr(name, data)
        return hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def run_install(self, digest, version="1.70.3", bin_dir=None):
        return installer.install(self.archive, version, digest, bin_dir or self.bin_dir)

    def test_verified_install_replaces_binary_without_executing_it(self):
        digest = self.make_archive()
        self.bin_dir.mkdir()
        destination = self.bin_dir / "rclone"
        destination.write_bytes(b"previous version")
        self.assertEqual(self.run_install(digest.upper(), version="v1.70.3"), destination)
        self.assertEqual(destination.read_bytes(), self.binary)
        self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o755)
        self.assertFalse(self.marker.exists())
        self.assertEqual(list(self.bin_dir.iterdir()), [destination])

    def test_digest_mismatch_precedes_zip_parsing_and_preserves_existing_binary(self):
        self.archive.write_bytes(b"not even a ZIP")
        self.bin_dir.mkdir()
        destination = self.bin_dir / "rclone"
        destination.write_bytes(b"previous version")
        with patch.object(installer.zipfile, "ZipFile") as parse:
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                self.run_install("0" * 64)
            parse.assert_not_called()
        self.assertEqual(destination.read_bytes(), b"previous version")

    def test_source_archive_changes_cannot_replace_verified_snapshot(self):
        digest = self.make_archive()
        original_zip_file = installer.zipfile.ZipFile

        def change_source_then_open_snapshot(path):
            self.archive.write_bytes(b"changed after verification")
            return original_zip_file(path)

        with patch.object(installer.zipfile, "ZipFile", side_effect=change_source_then_open_snapshot):
            destination = self.run_install(digest)
        self.assertEqual(destination.read_bytes(), self.binary)
        self.assertFalse(self.marker.exists())

    def test_invalid_zip_with_matching_digest_cannot_install(self):
        self.archive.write_bytes(b"not a release ZIP")
        digest = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        with self.assertRaises(zipfile.BadZipFile):
            self.run_install(digest)
        self.assertFalse(self.bin_dir.exists())

    def test_missing_or_malformed_digest_cannot_install(self):
        self.make_archive()
        for digest in ("", "a" * 63, "g" * 64):
            with self.subTest(digest=digest):
                with self.assertRaisesRegex(ValueError, "SHA-256"):
                    self.run_install(digest)
        self.assertFalse(self.bin_dir.exists())

    def test_mutable_beta_and_path_versions_are_rejected(self):
        digest = self.make_archive()
        for version in ("latest", "beta", "1.70.3-beta.1", "1.70.3/../../other"):
            with self.subTest(version=version):
                with self.assertRaisesRegex(ValueError, "stable release"):
                    self.run_install(digest, version)
        self.assertFalse(self.bin_dir.exists())

    def test_root_is_rejected_before_reading_archive(self):
        with patch.object(installer.os, "geteuid", return_value=0):
            with self.assertRaisesRegex(ValueError, "without sudo"):
                self.run_install("0" * 64)
        self.assertFalse(self.bin_dir.exists())

    def test_wrong_version_or_platform_member_cannot_install(self):
        for member in ("rclone-v1.70.2-linux-amd64/rclone", "rclone-v1.70.3-osx-arm64/rclone"):
            with self.subTest(member=member):
                digest = self.make_archive([(member, self.binary)])
                with self.assertRaisesRegex(ValueError, "exactly one binary"):
                    self.run_install(digest)
        self.assertFalse(self.bin_dir.exists())

    def test_duplicate_binary_members_cannot_install(self):
        digest = self.make_archive([(self.member, b"first"), (self.member, b"second")])
        with self.assertRaisesRegex(ValueError, "exactly one binary"):
            self.run_install(digest)
        self.assertFalse(self.bin_dir.exists())

    def test_symlink_and_empty_binary_members_cannot_install(self):
        link = zipfile.ZipInfo(self.member)
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        for entry in ((link, b"/some/other/binary"), (self.member, b"")):
            with self.subTest(entry=entry[0]):
                digest = self.make_archive([entry])
                with self.assertRaisesRegex(ValueError, "regular file"):
                    self.run_install(digest)
        self.assertFalse(self.bin_dir.exists())

    def test_unrelated_paths_and_scripts_are_never_extracted(self):
        escaped = self.root / "escaped"
        digest = self.make_archive([
            (self.member, self.binary), (str(escaped), b"absolute path"),
            ("../../escaped", b"traversal"), ("install.sh", self.binary),
        ])
        self.run_install(digest)
        self.assertFalse(escaped.exists())
        self.assertFalse(self.marker.exists())
        self.assertEqual(list(self.bin_dir.iterdir()), [self.bin_dir / "rclone"])

    def test_symlink_destination_is_not_followed_or_replaced(self):
        digest = self.make_archive()
        original = self.root / "original"
        original.write_bytes(b"untouched")
        self.bin_dir.mkdir()
        destination = self.bin_dir / "rclone"
        destination.symlink_to(original)
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.run_install(digest)
        self.assertTrue(destination.is_symlink())
        self.assertEqual(original.read_bytes(), b"untouched")

    def test_failed_atomic_replace_preserves_binary_and_cleans_pending_file(self):
        digest = self.make_archive()
        self.bin_dir.mkdir()
        destination = self.bin_dir / "rclone"
        destination.write_bytes(b"previous version")
        with patch.object(installer.os, "replace", side_effect=OSError("simulated failure")):
            with self.assertRaisesRegex(OSError, "simulated failure"):
                self.run_install(digest)
        self.assertEqual(destination.read_bytes(), b"previous version")
        self.assertEqual(list(self.bin_dir.iterdir()), [destination])

    def test_relative_destination_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "absolute path"):
            self.run_install("0" * 64, bin_dir=Path("relative"))

    def test_platform_mapping_preserves_supported_unix_targets(self):
        for system, machine, expected in (
            ("Darwin", "arm64", ("osx", "arm64")),
            ("Darwin", "x86_64", ("osx", "amd64")),
            ("FreeBSD", "amd64", ("freebsd", "amd64")),
            ("OpenBSD", "i386", ("openbsd", "386")),
            ("NetBSD", "aarch64", ("netbsd", "arm64")),
            ("Linux", "armv7l", ("linux", "arm-v7")),
            ("Linux", "armv6l", ("linux", "arm-v6")),
        ):
            with self.subTest(system=system, machine=machine):
                with patch.object(installer.platform, "system", return_value=system):
                    with patch.object(installer.platform, "machine", return_value=machine):
                        self.assertEqual(installer.release_platform(), expected)

    def test_legacy_no_argument_shell_entry_fails_closed(self):
        wrapper = Path(installer.__file__).with_name("install.sh")
        result = subprocess.run(["bash", str(wrapper)], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("--archive", result.stderr)
        self.assertIn("--sha256", result.stderr)
        self.assertFalse(self.bin_dir.exists())


if __name__ == "__main__":
    unittest.main()
