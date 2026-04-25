import os
from datetime import date

import boto3
import S2_ship_handling
import settings
from botocore import UNSIGNED
from botocore.client import Config


def list_s3_tiles():
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    today = date.today()
    prefix = settings.S3_PREFIX.format(
        year=today.year,
        month=today.month,
        day=today.day,
    )

    # TODO: DELETE this prefix
    # prefix = "tiles/39/R/VK/2026/4/18/0/R10m"
    prefix = "tiles/39/R/VK/2026/4/13/0/R10m"

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
        "B03": "blue",
        "B04": "green",
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


def main():
    os.makedirs(settings.INPUT_PATH, exist_ok=True)
    os.makedirs(settings.OUTPUT_PATH, exist_ok=True)

    print(f"Listing S3 tiles for {settings.DATE_STAMP}...")
    tiles = list_s3_tiles()
    if not tiles:
        print("No tiles found")
        return

    for tile in tiles:
        print(f"  {tile['Key']} - {tile['Size']} bytes")

    print("Downloading bands...")
    band_files = download_bands(tiles, settings.INPUT_PATH)

    if len(band_files) != 3:
        print(f"Expected 3 bands, got {len(band_files)}")
        return

    print(f"Blue: {band_files['blue']}")
    print(f"Green: {band_files['green']}")
    print(f"Red: {band_files['red']}")

    print("Cutting to ROI...")
    roi_image = S2_ship_handling.roi_cut_stack(
        band_files["blue"],
        band_files["green"],
        band_files["red"],
    )

    print("Tiling to dock chips...")
    S2_ship_handling.image_tiler(roi_image)

    print("Done!")


if __name__ == "__main__":
    main()
