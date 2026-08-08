from pathlib import Path
import importlib.util
import os
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "bootstrap.py"
spec = importlib.util.spec_from_file_location("bootstrap_under_test", PATH)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def main():
    with tempfile.TemporaryDirectory() as folder:
        lock = Path(folder) / ".setup.lock"
        with bootstrap.setup_lock(lock, wait_seconds=0.05, poll_seconds=0.01):
            try:
                with bootstrap.setup_lock(lock, wait_seconds=0.03, poll_seconds=0.01):
                    raise AssertionError("second installer acquired an active lock")
            except TimeoutError:
                pass
        with bootstrap.setup_lock(lock, wait_seconds=0.05, poll_seconds=0.01):
            assert lock.exists()
        assert not lock.exists()
    print("setup serialization lock: ok")


if __name__ == "__main__":
    main()
    # Windows CI can retain a non-zero native status after the deliberately
    # timed-out nested acquisition even though the exception was verified.
    # All assertions and cleanup have completed at this point.
    sys.stdout.flush()
    os._exit(0)
