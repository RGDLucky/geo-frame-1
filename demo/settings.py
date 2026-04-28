import os
from datetime import date

# Hardcoded location parameters (Ras Tanura Oil Terminal area)
UTM_ZONE = "39"
LATITUDE_BAND = "R"
GRID_SQUARE = "VK"
SEQUENCE = "0"

S3_BUCKET = os.getenv("S3_BUCKET", "sentinel-s2-l2a")
S3_PREFIX = f"tiles/{UTM_ZONE}/{LATITUDE_BAND}/{GRID_SQUARE}/{{year}}/{{month}}/{{day}}/{SEQUENCE}/R10m"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE_DIR, os.getenv("INPUT_DIR", "s3_temp"))
OUTPUT_PATH = os.path.join(BASE_DIR, os.getenv("OUTPUT_DIR", "output"))
ASSETS_PATH = os.path.join(BASE_DIR, "assets")

# ML pipeline paths
ML_OUTPUT_DIR = os.path.join(BASE_DIR, "../ml/data/unlabeled")
PNG_CHIPS_DIR = os.path.join(OUTPUT_PATH, "png_chips")

ROI_BOX = "ROI_box.shp"
DOCKS_SHP = "RasTanura Oil Terminal.shp"

today = date.today()
DATE_STAMP = f"{today.year}{today.month}{today.day}"
ROI_3B_IMAGE = "tmp_roi_3b_image.tif"
FILENAME_TEMPLATE = "{attr_name}_{date_stamp}.tif"
