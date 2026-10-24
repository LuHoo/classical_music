import subprocess
import os


def test_probe_git():
    for args in (["git", "rev-parse", "HEAD"], ["git", "status", "--porcelain"]):
        r = subprocess.run(args, capture_output=True, text=True)
        print("PROBE", args, "rc=", r.returncode, "out=", r.stdout.strip()[:40],
              "err=", r.stderr.strip()[:400])
    print("PROBE CWD", os.getcwd())
