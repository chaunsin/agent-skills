#!/usr/bin/env python3
"""Run Git inspection with configured execution helpers disabled (Python 3.8+)."""

import argparse
import os
from pathlib import Path
import subprocess
import sys


COMMANDS = ("status", "rev-parse", "for-each-ref", "describe", "log", "show", "diff", "blame", "ls-files")
BASE_OPTIONS = [
    "--no-pager", "-c", "core.fsmonitor=false", "-c", "log.showSignature=false",
    "-c", "submodule.recurse=false", "-c", "format.pretty=medium",
    # Pretty-format signature placeholders can invoke verification independently
    # of log.showSignature. No configured verification program may execute.
    "-c", "gpg.program=", "-c", "gpg.openpgp.program=",
    "-c", "gpg.x509.program=", "-c", "gpg.ssh.program=",
]


def inspection_command(repo, command, arguments, env):
    if command not in COMMANDS:
        raise ValueError("Unsupported inspection command: " + command)
    options = list(BASE_OPTIONS)
    # -z preserves driver names containing whitespace; only data is passed to Git.
    result = subprocess.run(
        ["git", *options, "config", "--null", "--name-only", "--get-regexp",
         r"^filter\..*\.(clean|process|required)$"],
        cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode not in (0, 1):
        raise ValueError("Cannot inspect Git filter configuration; inspection stopped.")
    drivers = {key.rsplit(b".", 1)[0].decode("utf-8", "surrogateescape")
               for key in result.stdout.split(b"\0") if key}
    for driver in sorted(drivers):
        if "=" in driver:
            # Git permits '=' in subsection names, but -c splits at the first '='.
            raise ValueError("Cannot safely override a Git filter driver containing '='; inspect files as text.")
        options.extend(["-c", driver + ".clean=", "-c", driver + ".process=",
                        "-c", driver + ".required=false"])

    split = next((index for index, value in enumerate(arguments)
                  if value in ("--", "--end-of-options")), len(arguments))
    before, paths = arguments[:split], arguments[split:]
    guards = []
    if command in ("diff", "log", "show"):
        guards += ["--no-ext-diff", "--no-textconv", "--ignore-submodules=dirty", "--submodule=short"]
    if command in ("log", "show"):
        guards += ["--no-show-signature"]
    if command == "blame":
        guards += ["--no-textconv"]
    if command == "status":
        guards += ["--ignore-submodules=dirty"]
    # Final options win over earlier enabling flags, before Git's path terminator.
    return ["git", *options, command, *before, *guards, *paths]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("git_args", nargs=argparse.REMAINDER, metavar="COMMAND [ARG ...]",
                        help="Inspection command: " + ", ".join(COMMANDS))
    args = parser.parse_args()
    if not args.git_args:
        parser.error("An inspection command is required.")
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        command = inspection_command(args.repo, args.git_args[0], args.git_args[1:], env)
        return subprocess.run(command, cwd=args.repo, env=env).returncode
    except (OSError, ValueError) as error:
        print("Git inspection failed: {}".format(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
