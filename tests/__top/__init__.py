"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

import os
import sys
from pathlib import Path

VERBOSE: bool = os.getenv("VERBOSE") or False

if VERBOSE:
    print("👋 init test paths for __top")


root_directory = Path(__file__).resolve().parent.parent.parent
src_directory = os.path.join(root_directory, "src")
# inject src path to python search path
sys.path.insert(0, src_directory)

if VERBOSE:
    print("")
    for p in sys.path:
        print(f"👉 {p}")
