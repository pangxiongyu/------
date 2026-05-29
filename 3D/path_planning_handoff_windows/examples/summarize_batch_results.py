from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.eval.report import export_batch_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize long-form batch experiment metrics.")
    parser.add_argument(
        "--input",
        default=str(ROOT / "outputs" / "batch_experiments" / "batch_metrics_long.csv"),
        help="Path to batch_metrics_long.csv.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "outputs" / "batch_experiments"),
        help="Directory for batch_summary.csv and batch_summary.md.",
    )
    args = parser.parse_args()

    summary_rows = export_batch_summary(args.input, args.output_dir)
    print("Batch summary exported")
    print(
        {
            "row_count": len(summary_rows),
            "summary_csv": str(Path(args.output_dir) / "batch_summary.csv"),
            "summary_md": str(Path(args.output_dir) / "batch_summary.md"),
        }
    )


if __name__ == "__main__":
    main()
