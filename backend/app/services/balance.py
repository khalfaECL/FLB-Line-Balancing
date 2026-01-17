from pathlib import Path
from typing import Any, Dict

import sys


def _find_repo_root(start: Path) -> Path:
    for parent in [start] + list(start.parents):
        if (parent / "mte4.py").exists():
            return parent
    return start.parents[2] if len(start.parents) > 2 else start


ROOT_DIR = _find_repo_root(Path(__file__).resolve())
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

import mte4


def run_balance(file_path: str, method: str) -> Dict[str, Any]:
    method = method.upper()
    if method == "MTE":
        return mte4.mte_balance_by_file(file_path)
    if method == "SPT":
        return mte4.spt_balance_by_file(file_path)
    if method == "RPW":
        return mte4.rpw_balance_by_file(file_path)
    raise ValueError(f"Unsupported method: {method}")


def run_all_methods(file_path: str) -> Dict[str, Dict[str, Any]]:
    return {
        "MTE": run_balance(file_path, "MTE"),
        "SPT": run_balance(file_path, "SPT"),
        "RPW": run_balance(file_path, "RPW"),
    }
