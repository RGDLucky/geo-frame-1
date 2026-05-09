from io import BytesIO
from PIL import Image


def convert_tiff_to_png(tiff_bytes: bytes) -> bytes:
    img = Image.open(BytesIO(tiff_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def convert_image_bytes_to_png(image_bytes: bytes, source_format: str = "TIFF") -> bytes:
    img = Image.open(BytesIO(image_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    output = BytesIO()
    output_format = source_format.upper()
    if output_format == "TIFF":
        output_format = "PNG"
    img.save(output, format=output_format)
    return output.getvalue()
