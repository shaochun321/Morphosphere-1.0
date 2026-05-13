"""Helper to materialize VFS files into real filesystem for Python import."""
import os, sys

BASE = os.path.join("src", "morphosphere", "active_exec")
RUNTIME = os.path.join(BASE, "runtime")

def read_vfs_file(path):
    """Read file that may exist in VFS but not in real FS."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Try listing parent dir to see if file exists in VFS
        parent = os.path.dirname(path)
        fname = os.path.basename(path)
        if os.path.isdir(parent) and fname in os.listdir(parent):
            # File exists in VFS but not accessible
            return None
        return None

def materialize():
    """Create real copies of files that are stuck in the tar VFS."""
    # Files we need to materialize
    targets = {
        os.path.join(RUNTIME, "confirmation", "pr_graph_engine.py"): True,
        os.path.join(RUNTIME, "ledger", "routing_engine.py"): True,
        os.path.join(BASE, "perturbations", "definitions.py"): True,
    }
    
    for path, needed in targets.items():
        exists = os.path.exists(path)
        print(f"  {path}: exists={exists}")
        if not exists and needed:
            print(f"    -> NEEDS MATERIALIZATION")

if __name__ == "__main__":
    materialize()
