#!/usr/bin/env python
"""
Utility script to automatically download and extract the official real CICIDS2017 Machine Learning dataset.
Downloads from the University of New Brunswick (UNB) direct files directory.
"""
import sys
import os
import zipfile
import urllib.request
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.utils import ensure_directory


def download_progress_hook(count, block_size, total_size):
    """Callback function to show progress bar during download."""
    global last_percent
    percent = int(count * block_size * 100 / total_size)
    if percent != last_percent:
        sys.stdout.write(f"\rDownloading... {percent}% completed ({count * block_size / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)")
        sys.stdout.flush()
        last_percent = percent


def main():
    global last_percent
    last_percent = -1
    
    dataset_url = "http://205.174.165.80/CICDataset/CIC-IDS-2017/Dataset/MachineLearningCVE.zip"
    raw_dir = PROJECT_ROOT / "data" / "raw"
    ensure_directory(raw_dir)
    
    zip_path = raw_dir / "MachineLearningCVE.zip"

    print("==================================================")
    print("Network Intrusion Detection System - Dataset Downloader")
    print("==================================================")
    print(f"Source URL: {dataset_url}")
    print(f"Destination: {raw_dir.resolve()}")
    print("--------------------------------------------------")
    print("WARNING: The dataset zip file is ~230 MB and will extract")
    print("to 8 CSV files totaling ~3.1 GB of raw telemetry data.")
    print("--------------------------------------------------")

    try:
        # 1. Download the zip file
        print("Starting download. Please wait...")
        urllib.request.urlretrieve(dataset_url, zip_path, reporthook=download_progress_hook)
        print("\nDownload completed successfully!")

        # 2. Extract the zip file
        print("Extracting files... This might take a few moments.")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # The zip contains a directory named "MachineLearningCVE" containing the 8 CSVs.
            # We want to extract them directly into data/raw/
            for file_info in zip_ref.infolist():
                # Skip directories
                if file_info.is_dir():
                    continue
                # Strip directory prefixes to extract directly to data/raw/
                filename = Path(file_info.filename).name
                target_path = raw_dir / filename
                with zip_ref.open(file_info) as source, open(target_path, "wb") as target:
                    target.write(source.read())
                print(f" extracted: {filename}")

        # 3. Clean up the zip file
        print("Cleaning up temporary zip file...")
        if zip_path.exists():
            zip_path.unlink()

        # 4. Remove the synthetic data file if it exists to avoid pollution
        synthetic_file = raw_dir / "synthetic_cicids2017.csv"
        if synthetic_file.exists():
            synthetic_file.unlink()
            print("Removed temporary mock dataset file.")

        print("--------------------------------------------------")
        print("Real CICIDS2017 dataset is fully loaded and ready!")
        print("Run the EDA script to analyze the real data:")
        print("  .venv\\Scripts\\python.exe scripts\\run_eda.py")
        print("==================================================")

    except KeyboardInterrupt:
        print("\n[INFO] Download cancelled by user.")
        if zip_path.exists():
            zip_path.unlink()
    except Exception as e:
        print(f"\n[ERROR] An error occurred during download/extraction: {e}")
        if zip_path.exists():
            zip_path.unlink()
        sys.exit(1)


if __name__ == "__main__":
    main()
