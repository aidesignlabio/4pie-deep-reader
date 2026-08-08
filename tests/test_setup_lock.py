from pathlib import Path
import importlib.util
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "bootstrap.py"
spec = importlib.util.spec_from_file_location("bootstrap_under_test", PATH)
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def main():
    original_pid_check = bootstrap._pid_is_alive
    bootstrap._pid_is_alive = lambda pid: True
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
    bootstrap._pid_is_alive = original_pid_check
    print("setup serialization lock: ok")


if __name__ == "__main__":
    main()
