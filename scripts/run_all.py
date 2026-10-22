"""Re-run every notebook in order, refreshing its outputs, figures and tables, then the data dictionary.

    python scripts/run_all.py                 # all notebooks
    python scripts/run_all.py 4.1 4.2         # only notebooks whose names start with these ids
    python scripts/run_all.py --skip 5.1      # all except the literature review (slow model download)

Cells tagged `skip-execution` (the 2.1 appendix, which needs internet) are not run.
Stops at the first notebook that raises an error and leaves it unsaved.
"""
import argparse
import subprocess
import sys
import time

import nbformat
from nbclient import NotebookClient

from serl_energy.config import PROJECT_DIR

NOTEBOOK_DIR = PROJECT_DIR / "notebooks"


def notebooks(only: list[str], skip: list[str]):
    paths = sorted(NOTEBOOK_DIR.glob("[0-9]*.ipynb"), key=lambda p: [int(x) for x in p.name.split("-")[0].split(".")])
    if only:
        paths = [p for p in paths if any(p.name.startswith(o + "-") for o in only)]
    return [p for p in paths if not any(p.name.startswith(s + "-") for s in skip)]


def run(path) -> float:
    start = time.time()
    nb = nbformat.read(path, as_version=4)
    NotebookClient(nb, timeout=None, kernel_name="python3", resources={"metadata": {"path": str(NOTEBOOK_DIR)}}).execute()
    nbformat.write(nb, path)
    return time.time() - start


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("only", nargs="*", help="notebook ids to run, e.g. 1.1 4.2 (default: all)")
    parser.add_argument("--skip", nargs="*", default=[], help="notebook ids to skip")
    args = parser.parse_args()
    for path in notebooks(args.only, args.skip):
        print(f"running {path.name} ...", flush=True)
        print(f"  done in {run(path):.0f} s", flush=True)
    subprocess.run([sys.executable, str(PROJECT_DIR / "scripts" / "build_data_dictionary.py")], check=True)


if __name__ == "__main__":
    main()
