# CLI Runner for KYO QA Knowledge Tool
import argparse
from datetime import datetime
from pathlib import Path

from processing_engine import process_folder, process_zip_archive
from logging_utils import setup_logger
from file_utils import ensure_folders

logger = setup_logger("cli")

def timestamped_copy(filepath):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(filepath)
    new_path = out_path.with_name(f"{out_path.stem}_{ts}{out_path.suffix}")
    return new_path

def main():
    parser = argparse.ArgumentParser(description="KYO QA ServiceNow CLI Tool")
    parser.add_argument("--folder", help="Path to folder of PDFs")
    parser.add_argument("--zip", help="Path to a zip file of PDFs")
    parser.add_argument("--excel", help="Path to existing Excel template")
    args = parser.parse_args()

    # Ensure required output folders exist before processing
    ensure_folders()

    if not args.excel or not Path(args.excel).exists():
        print("\nERROR: You must provide a valid Excel file using --excel\n")
        return

    output_excel = timestamped_copy(args.excel)
    Path(args.excel).rename(output_excel)
    print(f"Using working copy: {output_excel}")

    if args.folder:
        print(f"Processing folder: {args.folder}")
        process_folder(args.folder, output_excel, print, print, print, print, lambda: False)
    elif args.zip:
        print(f"Processing zip archive: {args.zip}")
        process_zip_archive(args.zip, output_excel, print, print, print, print, lambda: False)
    else:
        print("\nERROR: You must specify either --folder or --zip\n")
        return

    print("\n✅ Done. Updated Excel saved to:", output_excel)

if __name__ == "__main__":
    main()
