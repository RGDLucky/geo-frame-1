import os
from datetime import date, timedelta

import boto3
import S2_ship_handling
import settings
from botocore import UNSIGNED
from botocore.client import Config


def list_s3_tiles(target_date=None):
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    if target_date is None:
        target_date = date.today()
    prefix = settings.S3_PREFIX.format(
        year=target_date.year,
        month=target_date.month,
        day=target_date.day,
    )

    response = s3.list_objects_v2(
        Bucket=settings.S3_BUCKET,
        Prefix=prefix,
    )
    print(f"Using prefix: {prefix}")
    return response.get("Contents", [])


def download_bands(objects, local_dir):
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    os.makedirs(local_dir, exist_ok=True)

    band_map = {
        "B02": "blue",
        "B03": "green",
        "B08": "red",
    }

    local_files = {}
    for obj in objects:
        key = obj["Key"]
        for band, label in band_map.items():
            if band in key:
                local_path = os.path.join(local_dir, os.path.basename(key))
                print(f"Downloading {key}...")
                s3.download_file(settings.S3_BUCKET, key, local_path)
                local_files[label] = local_path
                break

    return local_files


def process_date(target_date):
    """Process a single date: download, create chips, convert to PNG"""
    date_stamp = f"{target_date.year}{target_date.month}{target_date.day}"
    print(f"\n{'='*50}")
    print(f"Processing date: {target_date} (stamp: {date_stamp})")
    print(f"{'='*50}")

    # Update settings for this date
    settings.DATE_STAMP = date_stamp

    print(f"Listing S3 tiles...")
    tiles = list_s3_tiles(target_date)
    if not tiles:
        print(f"No tiles found for {target_date}, skipping...")
        return False

    for tile in tiles:
        print(f"  {tile['Key']} - {tile['Size']} bytes")

    # Create date-specific input/output dirs
    date_input_dir = os.path.join(settings.INPUT_PATH, date_stamp)
    date_output_dir = os.path.join(settings.OUTPUT_PATH, date_stamp)

    print("Downloading bands...")
    band_files = download_bands(tiles, date_input_dir)

    if len(band_files) != 3:
        print(f"Expected 3 bands, got {len(band_files)}. Skipping...")
        return False

    print(f"Blue: {band_files['blue']}")
    print(f"Green: {band_files['green']}")
    print(f"Red: {band_files['red']}")

    print("Cutting to ROI...")
    roi_image = S2_ship_handling.roi_cut_stack(
        band_files["blue"],
        band_files["green"],
        band_files["red"],
        output_dir=date_output_dir,
    )

    print("Tiling to dock chips...")
    chips_dir = S2_ship_handling.image_tiler(
        roi_image, chips_dir=os.path.join(date_output_dir, "chips")
    )

    print("Converting chips to PNG for ML...")
    png_dir = S2_ship_handling.convert_chips_to_png(
        output_dir=date_output_dir, date_stamp=date_stamp
    )
    print(f"PNG chips saved to: {png_dir}")

    return True


def main():
    os.makedirs(settings.INPUT_PATH, exist_ok=True)
    os.makedirs(settings.OUTPUT_PATH, exist_ok=True)

    # Process past 2 years (730 days)
    end_date = date.today()
    # start_date = end_date - timedelta(days=730)
    start_date = end_date - timedelta(days=30)

    print(f"Processing data from {start_date} to {end_date} (past 2 years)")

    total_days = (end_date - start_date).days + 1
    processed_days = 0
    skipped_days = 0

    current_date = start_date
    while current_date <= end_date:
        try:
            success = process_date(current_date)
            if success:
                processed_days += 1
            else:
                skipped_days += 1
        except Exception as e:
            print(f"Error processing {current_date}: {e}")
            skipped_days += 1

        current_date += timedelta(days=1)

    print(f"\n{'='*50}")
    print(f"Processing complete!")
    print(f"Total days in range: {total_days}")
    print(f"Days processed successfully: {processed_days}")
    print(f"Days skipped (no data/errors): {skipped_days}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
