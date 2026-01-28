import subprocess
import os
import sys

processes = {}

def start_ingestion():
    """
    Launch ingest.py and ingest_depth.py in background subprocesses.
    Prevents duplicate launches.
    """
    global processes

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_python = sys.executable  # uses current venv python

    scripts = {
        "trades": os.path.join(base_dir, "src", "ingest.py"),
        "depth": os.path.join(base_dir, "src", "ingest_depth.py"),
    }

    for key, script in scripts.items():
        if key not in processes or processes[key].poll() is not None:
            processes[key] = subprocess.Popen(
                [venv_python, script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

def is_running(key):
    return key in processes and processes[key].poll() is None
