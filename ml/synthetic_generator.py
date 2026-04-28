import os
import cv2
import numpy as np
from PIL import Image
import random


def overlay_boat(background_img, boat_img, scale_range=(0.8, 1.2), rotation_range=(0, 360)):
    bg = background_img.copy()
    h, w = bg.shape[:2]
    boat_h, boat_w = boat_img.shape[:2]
    scale = random.uniform(*scale_range)
    new_w = int(boat_w * scale)
    new_h = int(boat_h * scale)
    boat_resized = cv2.resize(boat_img, (new_w, new_h))
    angle = random.uniform(*rotation_range)
    center = (new_w // 2, new_h // 2)
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    boat_rotated = cv2.warpAffine(boat_resized, rot_mat, (new_w, new_h), flags=cv2.INTER_LINEAR)
    max_x = w - new_w
    max_y = h - new_h
    if max_x <= 0 or max_y <= 0:
        return bg
    x = random.randint(0, max_x)
    y = random.randint(0, max_y)
    alpha = boat_rotated[:, :, 3] / 255.0 if boat_rotated.shape[2] == 4 else np.ones((new_h, new_w), dtype=np.float32)
    for c in range(3):
        bg[y:y+new_h, x:x+new_w, c] = (1 - alpha) * bg[y:y+new_h, x:x+new_w, c] + alpha * boat_rotated[:, :, c]
    return bg.astype(np.uint8)


def add_cloud_texture(img, cloud_mask, opacity_range=(0.3, 0.7)):
    result = img.copy().astype(np.float32)
    cloud = cv2.resize(cloud_mask, (img.shape[1], img.shape[0]))
    cloud = cloud.astype(np.float32) / 255.0
    opacity = random.uniform(*opacity_range)
    result = (1 - opacity * cloud[:, :, np.newaxis]) * result + (opacity * cloud[:, :, np.newaxis]) * np.array([200, 200, 210], dtype=np.float32)
    return np.clip(result, 0, 255).astype(np.uint8)


def generate_synthetic_samples(real_images, output_dir, num_per_image=2, class_type='boat_docked'):
    os.makedirs(output_dir, exist_ok=True)
    generated_paths = []
    for i, (bg_path, boat_path) in enumerate(real_images):
        bg = cv2.imread(bg_path)
        if bg is None:
            continue
        if class_type == 'boat_docked' and boat_path:
            boat = cv2.imread(boat_path, cv2.IMREAD_UNCHANGED)
            if boat is None:
                continue
            synthetic = overlay_boat(bg, boat)
        else:
            synthetic = bg
        for j in range(num_per_image):
            out_path = os.path.join(output_dir, f'synthetic_{i}_{j}.png')
            cv2.imwrite(out_path, synthetic)
            generated_paths.append(out_path)
    return generated_paths
