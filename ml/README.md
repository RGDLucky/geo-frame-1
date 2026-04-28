# ML Training Pipeline

## Overview
This directory contains the training pipeline for the dock boat detection model using EfficientNet-B2.

## Folder Structure
```
ml/
├── data/
│   ├── train/
│   │   ├── boat_docked/
│   │   ├── no_boats/
│   │   └── too_cloudy/
│   ├── val/
│   │   ├── boat_docked/
│   │   ├── no_boats/
│   │   └── too_cloudy/
│   ├── test/
│   │   ├── boat_docked/
│   │   ├── no_boats/
│   │   └── too_cloudy/
│   └── dataset.csv
├── checkpoints/
├── model.py
├── dataset.py
├── train.py
├── synthetic_generator.py
├── config.yaml
└── requirements.txt
```

## Setup
```bash
pip install -r requirements.txt
```

For JP2 support, install OpenJPEG:
```bash
conda install -c conda-forge openjpeg
```

## Dataset CSV Format
Create `data/dataset.csv` with columns:
- `image_path`: Path relative to data_dir in config.yaml
- `label`: 0=boat_docked, 1=no_boats, 2=too_cloudy
- `split`: train/val/test
- `is_synthetic`: True/False

## Training
```bash
python train.py
```

## Image Labeling GUI
Before training, use the labeling GUI to sort unlabeled images into classes:
```bash
python label_gui.py /path/to/unlabeled_images/
```
Or without argument (will prompt for directory):
```bash
python label_gui.py
```
**Controls:**
- `1` or "No Boat" button → labels as no_boats
- `2` or "Boat" button → labels as boat_docked
- `3` or "Too Cloudy" button → labels as too_cloudy
- `Ctrl+Z` or "Undo" button → reverts last label

Labeled images are moved to `data/train/{class}/` and entries are appended to `data/dataset.csv` automatically.

## Synthetic Data Generation
If you have <1k real images, use the synthetic generator:
```python
from synthetic_generator import generate_synthetic_samples
# Edit synthetic_generator.py with your image paths
```
