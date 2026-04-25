import os
from datetime import date

S3_BUCKET = os.getenv("S3_BUCKET", "sentinel-s2-l2a")
S3_PREFIX = os.getenv("S3_PREFIX", "tiles/39/R/VK/{year}/{month}/{day}/0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, os.getenv("INPUT_DIR", "s3_temp"))
OUTPUT_PATH = os.path.join(BASE_DIR, os.getenv("OUTPUT_DIR", "output"))
ASSETS_PATH = os.path.join(BASE_DIR, "assets")

ROI_BOX = "ROI_box.shp"
DOCKS_SHP = "RasTanura Oil Terminal.shp"

today = date.today()
DATE_STAMP = f"{today.year}{today.month}{today.day}"
ROI_3B_IMAGE = "tmp_roi_3b_image.tif"
FILENAME_TEMPLATE = "{attr_name}_{date_stamp}.tif"