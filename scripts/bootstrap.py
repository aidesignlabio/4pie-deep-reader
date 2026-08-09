#!/usr/bin/env python3
"""Install and verify the complete 4PIE runtime in .venv."""
import contextlib, os, platform, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
VENV=ROOT/".venv"
SETUP=ROOT/"scripts"/"vedic_engine"/"scripts"/"setup_env.py"
NODE=ROOT/"scripts"/"calculator"/"node"
FONT_DIR=ROOT/"assets"/"fonts"
FONT_FILE=FONT_DIR/"NotoSansTC-Variable.ttf"
FONT_URL="https://raw.githubusercontent.com/google/fonts/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf"
SETUP_LOCK=ROOT/".setup.lock"

def _pid_is_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except OSError:
        return False

@contextlib.contextmanager
def setup_lock(path=SETUP_LOCK, wait_seconds=None, poll_seconds=None):
    """Serialize setup runs so retries cannot start a second pip/npm install."""
    path=Path(path)
    wait_seconds=float(wait_seconds if wait_seconds is not None else os.getenv("FOURPIE_SETUP_LOCK_WAIT_SECONDS", "1200"))
    poll_seconds=float(poll_seconds if poll_seconds is not None else os.getenv("FOURPIE_SETUP_LOCK_POLL_SECONDS", "2"))
    deadline=time.monotonic()+max(0, wait_seconds)
    announced=False
    while True:
        try:
            fd=os.open(path, os.O_CREAT|os.O_EXCL|os.O_WRONLY)
            with os.fdopen(fd,"w",encoding="utf-8") as handle:
                handle.write(f"{os.getpid()}\n{time.time()}\n")
            print(f"SETUP_LOCK_ACQUIRED path={path}")
            break
        except FileExistsError:
            try:
                lines=path.read_text(encoding="utf-8").splitlines()
                owner=int(lines[0]) if lines else 0
                created=float(lines[1]) if len(lines)>1 else path.stat().st_mtime
            except (OSError, ValueError):
                owner, created=0, 0
            if not _pid_is_alive(owner) and time.time()-created>120:
                try:
                    path.unlink()
                    print(f"SETUP_STALE_LOCK_REMOVED path={path}")
                    continue
                except FileNotFoundError:
                    continue
                except OSError:
                    pass
            if not announced:
                print(f"SETUP_WAITING another installation is running (pid={owner}); do not start setup again.")
                announced=True
            if time.monotonic()>=deadline:
                raise TimeoutError("another 4PIE installation is still running; wait for it to finish, then run doctor")
            time.sleep(max(0.01,poll_seconds))
    try:
        yield
    finally:
        try:
            lines=path.read_text(encoding="utf-8").splitlines()
            if lines and int(lines[0])==os.getpid():
                path.unlink(missing_ok=True)
                print(f"SETUP_LOCK_RELEASED path={path}")
        except (OSError, ValueError):
            pass

def run(cmd, cwd=None):
    print("+", " ".join(map(str,cmd)))
    return subprocess.run(list(map(str,cmd)),cwd=cwd).returncode

def venv_python():
    return VENV/("Scripts/python.exe" if platform.system()=="Windows" else "bin/python")

def ensure_font():
    """Install the release-pinned Traditional Chinese font locally."""
    if FONT_FILE.is_file() and FONT_FILE.stat().st_size > 1_000_000:
        print(f"FONT_READY path={FONT_FILE}")
        return 0
    FONT_DIR.mkdir(parents=True,exist_ok=True)
    partial=FONT_FILE.with_suffix(".download")
    try:
        print(f"+ download {FONT_URL}")
        urllib.request.urlretrieve(FONT_URL,partial)
        if partial.stat().st_size <= 1_000_000:
            raise RuntimeError("downloaded font is unexpectedly small")
        partial.replace(FONT_FILE)
        print(f"FONT_READY path={FONT_FILE}")
        return 0
    except Exception as exc:
        partial.unlink(missing_ok=True)
        print(f"ERROR: unable to install Traditional Chinese font: {exc}")
        return 1

def main():
    try:
        with setup_lock():
            if run([sys.executable,SETUP,"--target",VENV]): return 1
            if ensure_font(): return 5
            if run([venv_python(),ROOT/"scripts"/"prepare_font_instances.py"]): return 5
            npm=shutil.which("npm.cmd" if platform.system()=="Windows" else "npm") or shutil.which("npm")
            if not npm:
                print("ERROR: Node.js/npm is required for Zi Wei calculation.")
                return 2
            if run([npm,"install","--no-audit","--no-fund"],cwd=NODE): return 2
            py=venv_python()
            if run([py,ROOT/"scripts"/"calculator"/"check_env.py"]): return 3
            if run([py,ROOT/"scripts"/"smoke_test.py"]): return 4
            print(f"4PIE_READY python={py}")
            return 0
    except TimeoutError as exc:
        print(f"ERROR: {exc}")
        return 6
if __name__=="__main__": raise SystemExit(main())
