import os

import geopandas as gpd
import numpy as np
import rasterio
import settings
from rasterio.mask import mask


def read_and_mask(band_path, geoms_json, shape_box):
    with rasterio.open(band_path) as src:
        if (
            shape_box.crs is not None
            and src.crs is not None
            and shape_box.crs != src.crs
        ):
            geoms_proj = shape_box.to_crs(src.crs).geometry.values
            geoms_json_local = [g.__geo_interface__ for g in geoms_proj]
        else:
            geoms_json_local = geoms_json

        data, transform = mask(src, geoms_json_local, crop=True, all_touched=True)
        profile = src.profile.copy()
        profile.update(
            {
                "height": data.shape[1],
                "width": data.shape[2],
                "transform": transform,
                "count": 1,
            }
        )
        return data[0], profile


def roi_cut_stack(in_blue, in_green, in_red, roi_box=None, output_dir=None):
    roi_box = roi_box or os.path.join(settings.ASSETS_PATH, settings.ROI_BOX)
    output_dir = output_dir or settings.OUTPUT_PATH

    shape_box = gpd.read_file(roi_box)
    geoms = shape_box.geometry.values
    geoms_json = [g.__geo_interface__ for g in geoms]

    b_band, profile = read_and_mask(in_blue, geoms_json, shape_box)
    g_band, _ = read_and_mask(in_green, geoms_json, shape_box)
    r_band, _ = read_and_mask(in_red, geoms_json, shape_box)

    rgb = np.stack([b_band, g_band, r_band], axis=0)

    profile.update({"count": 3, "dtype": rgb.dtype})

    out_tmp_3b_roi = os.path.join(output_dir, settings.ROI_3B_IMAGE)
    with rasterio.open(out_tmp_3b_roi, "w", **profile) as dst:
        dst.write(rgb)

    print("Saved:", out_tmp_3b_roi)
    return out_tmp_3b_roi


def image_tiler(out_tmp_3b_roi, docks_shp=None, chips_dir=None, date_stamp=None):
    docks_shp = docks_shp or os.path.join(settings.ASSETS_PATH, settings.DOCKS_SHP)
    chips_dir = chips_dir or os.path.join(
        settings.OUTPUT_PATH, settings.DATE_STAMP, "chips"
    )
    date_stamp = date_stamp or settings.DATE_STAMP

    id_field = "id"
    all_touched = True
    driver = "GTiff"

    os.makedirs(chips_dir, exist_ok=True)

    gdf = gpd.read_file(docks_shp)

    sel = gdf
    if sel.empty:
        raise SystemExit("No matching features found")

    with rasterio.open(out_tmp_3b_roi) as src:
        src_crs = src.crs
        if sel.crs is not None and src_crs is not None and sel.crs != src_crs:
            sel = sel.to_crs(src_crs)

        for _, row in sel.iterrows():
            id_val = row[id_field]
            terminal = str(row.get("Terminal")).replace(" ", "_")
            pier = str(row.get("Pier")).replace(" ", "_")
            dock = str(row.get("Dock")).replace(" ", "_")
            attr_name = terminal + "_" + pier + "_" + dock
            geom = [row.geometry.__geo_interface__]

            out_image, out_transform = mask(
                src, geom, crop=True, all_touched=all_touched
            )

            out_meta = src.meta.copy()
            out_meta.update(
                {
                    "driver": driver,
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                    "count": out_image.shape[0],
                }
            )

            fname = settings.FILENAME_TEMPLATE.format(
                attr_name=attr_name, date_stamp=date_stamp
            )
            out_path = os.path.join(chips_dir, fname)
            with rasterio.open(out_path, "w", **out_meta) as dst:
                dst.write(out_image)

            print(f"Wrote chip {out_path}")

