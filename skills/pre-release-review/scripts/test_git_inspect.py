"""Exercise Git helper boundaries in disposable local repositories."""

import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest


HELPER = Path(__file__).with_name("git_inspect.py").resolve()


class GitInspectionTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="git-inspect-test-")
        self.addCleanup(self.workspace.cleanup)
        self.root = Path(self.workspace.name)
        self.repo = self.root / "repo with spaces"
        self.repo.mkdir()
        self.env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        self.env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        self.git("init", "-q")
        self.git("config", "user.name", "Inspection test")
        self.git("config", "user.email", "test@example.invalid")
        self.path = "file with spaces.txt"
        (self.repo / ".gitattributes").write_text('"file with spaces.txt" filter=fixture diff=fixture\n')
        (self.repo / self.path).write_text("before\n")
        self.git("add", "--", ".gitattributes", self.path)
        self.git("commit", "-qm", "fixture")
        (self.repo / self.path).write_text("after\n")
        self.marker = self.root / "executed"
        self.program = self.root / "marker.py"
        self.program.write_text(
            "#!" + sys.executable + "\nfrom pathlib import Path\n"
            + "Path({!r}).write_text('executed')\n".format(str(self.marker))
            + "import sys\nsys.exit(1)\n"
        )
        self.program.chmod(0o755)

    def git(self, *args, **kwargs):
        return subprocess.run(["git", *args], cwd=self.repo, env=self.env,
                              capture_output=True, check=True, **kwargs)

    def inspect(self, *args, repo=None):
        return subprocess.run([sys.executable, str(HELPER), "--repo", str(repo or self.repo), *args],
                              cwd=self.root, env=self.env, capture_output=True, timeout=10)

    def test_clean_filter_is_not_executed_and_diff_blame_still_work(self):
        self.git("config", "filter.fixture.clean", shlex.quote(str(self.program)))
        self.git("config", "filter.fixture.required", "true")
        raw = subprocess.run(["git", "diff", "--no-ext-diff", "--no-textconv", "--", self.path],
                             cwd=self.repo, env=self.env, capture_output=True)
        self.assertNotEqual(raw.returncode, 0)
        self.assertTrue(self.marker.exists())
        self.marker.unlink()
        for command in ("diff", "blame"):
            result = self.inspect(command, "--", self.path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b"after", result.stdout)
            self.assertFalse(self.marker.exists())

    def test_process_filter_is_not_executed_even_when_required(self):
        self.git("config", "filter.fixture.process", shlex.quote(str(self.program)))
        self.git("config", "filter.fixture.required", "true")
        raw = subprocess.run(["git", "diff", "--", self.path], cwd=self.repo,
                             env=self.env, capture_output=True, timeout=10)
        self.assertNotEqual(raw.returncode, 0)
        self.assertTrue(self.marker.exists())
        self.marker.unlink()
        for command in ("diff", "blame"):
            result = self.inspect(command, "--", self.path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b"after", result.stdout)
            self.assertFalse(self.marker.exists())

    def test_diff_and_textconv_cannot_be_reenabled_by_arguments(self):
        self.git("config", "diff.fixture.command", shlex.quote(str(self.program)))
        self.git("config", "diff.fixture.textconv", shlex.quote(str(self.program)))
        for command, args in (
            ("diff", ["--ext-diff", "--textconv"]),
            ("log", ["-p", "--ext-diff", "--textconv"]),
            ("show", ["--ext-diff", "--textconv", "HEAD"]),
            ("blame", ["--textconv"]),
        ):
            result = self.inspect(command, *args, "--", self.path)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout)
            self.assertFalse(self.marker.exists())

    def test_automatic_and_explicit_signature_programs_are_disabled(self):
        original = self.git("cat-file", "commit", "HEAD").stdout
        header, body = original.split(b"\n\n", 1)
        signed = header + b"\ngpgsig -----BEGIN PGP SIGNATURE-----\n fake\n -----END PGP SIGNATURE-----\n\n" + body
        oid = self.git("hash-object", "-t", "commit", "--stdin", "-w", input=signed).stdout.strip()
        self.git("update-ref", "HEAD", oid.decode())
        self.git("config", "log.showSignature", "true")
        self.git("config", "gpg.program", str(self.program))
        self.git("config", "gpg.openpgp.program", str(self.program))
        self.git("log", "-1", "--oneline")
        self.assertTrue(self.marker.exists())
        self.marker.unlink()
        for command in ("log", "show"):
            result = self.inspect(command, "--show-signature", "--oneline", "-1")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(b"fixture", result.stdout)
            self.assertFalse(self.marker.exists())
        self.git("config", "format.pretty", "%G?")
        self.git("config", "pretty.verify", "%G?")
        for args in (("log", "-1"), ("log", "-1", "--format=%G?"),
                     ("show", "--pretty=verify", "--no-patch")):
            result = self.inspect(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(self.marker.exists())

    def test_unreadable_config_fails_before_inspection(self):
        with (self.repo / ".git" / "config").open("a") as config:
            config.write("\n[broken\n")
        result = self.inspect("diff", "--", self.path)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"configuration", result.stderr)

    def test_equals_in_filter_driver_fails_without_executing_it(self):
        (self.repo / ".gitattributes").write_text('"file with spaces.txt" filter=a=b\n')
        self.git("config", "filter.a=b.clean", shlex.quote(str(self.program)))
        self.git("config", "filter.a=b.required", "true")
        result = self.inspect("diff", "--", self.path)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(b"inspect files as text", result.stderr)
        self.assertFalse(self.marker.exists())

    def test_noninspection_command_is_rejected(self):
        before = self.git("rev-parse", "HEAD").stdout
        result = self.inspect("reset", "--hard", "HEAD")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(before, self.git("rev-parse", "HEAD").stdout)
        self.assertEqual((self.repo / self.path).read_text(), "after\n")

    def test_discovery_commands_and_staged_diff_remain_available(self):
        for args in (("status", "--short"), ("rev-parse", "--show-toplevel"),
                     ("for-each-ref", "--format=%(refname)"), ("describe", "--always"),
                     ("ls-files", "--stage")):
            result = self.inspect(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout)
        self.git("add", "--", self.path)
        result = self.inspect("diff", "--cached", "--", self.path)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"+after", result.stdout)
        result = self.inspect("rev-parse", "--verify", "--end-of-options", "HEAD^{commit}")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_submodule_worktrees_are_not_recursed_but_gitlinks_are_reported(self):
        outer = self.root / "outer"
        outer.mkdir()
        for args in (("init", "-q"), ("config", "user.name", "Test"),
                     ("config", "user.email", "test@example.invalid"),
                     ("-c", "protocol.file.allow=always", "submodule", "add", str(self.repo), "sub"),
                     ("commit", "-qm", "submodule")):
            subprocess.run(["git", *args], cwd=outer, env=self.env, check=True, capture_output=True)
        sub = outer / "sub"
        for key, value in (("filter.fixture.clean", shlex.quote(str(self.program))),
                           ("filter.fixture.required", "true")):
            subprocess.run(["git", "config", key, value], cwd=sub, env=self.env, check=True)
        (sub / self.path).write_text("after!\n")
        raw = subprocess.run(["git", "diff"], cwd=outer, env=self.env, capture_output=True)
        self.assertTrue(self.marker.exists(), raw.stderr)
        self.marker.unlink()
        for command in ("status", "diff"):
            result = self.inspect(command, repo=outer)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(self.marker.exists())
        # A different submodule HEAD must still be reported, without checking its files.
        tree = self.git("rev-parse", "HEAD^{tree}").stdout.strip().decode()
        new_head = self.git("commit-tree", tree, "-p", "HEAD", input=b"next\n").stdout.strip()
        # The new object is in the source repo, but not referenced; copy via a local ref.
        self.git("update-ref", "refs/heads/test-next", new_head.decode())
        subprocess.run(["git", "fetch", "origin", "test-next"], cwd=sub, env=self.env, check=True, capture_output=True)
        subprocess.run(["git", "update-ref", "HEAD", new_head.decode()], cwd=sub, env=self.env, check=True)
        result = self.inspect("diff", repo=outer)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"Subproject commit", result.stdout)
        self.assertFalse(self.marker.exists())


if __name__ == "__main__":
    unittest.main()
