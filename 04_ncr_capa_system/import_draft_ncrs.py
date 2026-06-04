"""
import_draft_ncrs.py

Imports Project 3 GD&T draft_ncrs.csv into the NCR/CAPA database.

Usage:

Automatic mode:
    python import_draft_ncrs.py

Manual override:
    python import_draft_ncrs.py path/to/draft_ncrs.csv
"""

from pathlib import Path
import sys

from database import init_db, import_draft_ncrs

# Default Project 3 integration path
DEFAULT_DRAFT_NCR_PATH = Path(
    "/workspaces/drone-manufacturing-quality-portfolio/"
    "drone-manufacturing-quality-portfolio/"
    "03_gdt_inspection_system/"
    "draft_ncrs.csv"
)


def get_csv_path():
    """
    Priority:
    1. User-supplied CLI path
    2. Default Project 3 integration path
    """

    if len(sys.argv) == 2:
        return Path(sys.argv[1])

    return DEFAULT_DRAFT_NCR_PATH


def main():
    csv_path = get_csv_path()

    if not csv_path.exists():
        print("\nERROR: draft_ncrs.csv not found.")
        print(f"Expected location:\n{csv_path}\n")

        print("Options:")
        print("1. Generate draft_ncrs.csv from Project 3")
        print("2. Supply a custom file path")
        print(
            "   python import_draft_ncrs.py /path/to/draft_ncrs.csv"
        )

        raise SystemExit(1)

    print(f"\nImporting draft NCRs from:\n{csv_path}\n")

    init_db()

    imported, skipped = import_draft_ncrs(str(csv_path))

    print("Import Complete")
    print("---------------------------")
    print(f"Imported: {imported}")
    print(f"Skipped:  {skipped}")
    print("---------------------------")


if __name__ == "__main__":
    main()