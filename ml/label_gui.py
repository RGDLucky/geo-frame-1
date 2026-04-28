"""
Dock Boat Image Labeler GUI

Usage:
    python label_gui.py [unlabeled_images_directory]

Description:
    A Tkinter-based tool to label unlabeled dock satellite images into 3 classes:
    - Boat docked (label 0, key '2' or "Boat" button)
    - No boats (label 1, key '1' or "No Boat" button)
    - Too cloudy (label 2, key '3' or "Too Cloudy" button)

    Labeled images are moved to ml/data/train/{class}/ and entries are automatically
    appended to ml/data/dataset.csv in the format:
    image_path, label, split, is_synthetic

Controls:
    - Keyboard: 1 (No Boat), 2 (Boat), 3 (Too Cloudy), Ctrl+Z (Undo last label)
    - GUI Buttons: Click the corresponding class button or "Undo" button

Arguments:
    unlabeled_images_directory: Optional path to folder containing unlabeled images
                              (supports .jp2, .png, .jpg, .jpeg)
                              If omitted, a directory chooser dialog will open.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import glymur
from PIL import Image, ImageTk
import shutil
import os
import csv
import sys
import glob


class LabelGUI:
    def __init__(self, root, unlabeled_dir=None):
        self.root = root
        self.root.title("Dock Boat Image Labeler")
        self.root.geometry("600x550")

        self.unlabeled_dir = unlabeled_dir
        self.image_list = []
        self.current_index = -1
        self.history = []

        self.ml_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.ml_dir, "data")
        self.train_dir = os.path.join(self.data_dir, "train")
        self.csv_path = os.path.join(self.data_dir, "dataset.csv")

        for cls in ["boat_docked", "no_boats", "too_cloudy"]:
            os.makedirs(os.path.join(self.train_dir, cls), exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)

        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["image_path", "label", "split", "is_synthetic"])

        self.setup_ui()
        if self.unlabeled_dir:
            self.load_image_list()
        else:
            self.select_directory()

    def setup_ui(self):
        self.img_label = tk.Label(self.root)
        self.img_label.pack(pady=10)

        self.progress_label = tk.Label(self.root, text="Progress: 0 / 0 images labeled")
        self.progress_label.pack()

        self.path_label = tk.Label(self.root, text="Current: No directory selected", wraplength=500)
        self.path_label.pack(pady=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="No Boat (1)", width=15, command=lambda: self.label_image(1)).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Boat (2)", width=15, command=lambda: self.label_image(0)).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Too Cloudy (3)", width=15, command=lambda: self.label_image(2)).grid(row=0, column=2, padx=5)

        self.undo_btn = tk.Button(self.root, text="Undo (Ctrl+Z)", width=30, command=self.undo_last, state=tk.DISABLED)
        self.undo_btn.pack(pady=5)

        if not self.unlabeled_dir:
            tk.Button(self.root, text="Select Unlabeled Directory", command=self.select_directory).pack(pady=5)

        self.root.bind('1', lambda e: self.label_image(1))
        self.root.bind('2', lambda e: self.label_image(0))
        self.root.bind('3', lambda e: self.label_image(2))
        self.root.bind('<Control-z>', lambda e: self.undo_last())

    def select_directory(self):
        self.unlabeled_dir = filedialog.askdirectory(title="Select Unlabeled Images Directory")
        if self.unlabeled_dir:
            self.load_image_list()
        else:
            messagebox.showwarning("No Directory", "No directory selected.")

    def load_image_list(self):
        supported = ('*.jp2', '*.png', '*.jpg', '*.jpeg')
        self.image_list = []
        for ext in supported:
            self.image_list.extend(glob.glob(os.path.join(self.unlabeled_dir, ext)))
            self.image_list.extend(glob.glob(os.path.join(self.unlabeled_dir, ext.upper())))
        self.image_list = list(set(self.image_list))
        if not self.image_list:
            messagebox.showinfo("No Images", "No supported images found in directory.")
            return
        self.current_index = 0
        self.show_image()
        self.update_progress()

    def show_image(self):
        if self.current_index < 0 or self.current_index >= len(self.image_list):
            self.img_label.config(image='')
            self.path_label.config(text="No more images to label.")
            return
        img_path = self.image_list[self.current_index]
        self.path_label.config(text=f"Current: {img_path}")
        try:
            if img_path.lower().endswith('.jp2'):
                jp2 = glymur.Jp2k(img_path)
                img = Image.fromarray(jp2[:])
            else:
                img = Image.open(img_path)
            img.thumbnail((400, 400))
            self.tk_img = ImageTk.PhotoImage(img)
            self.img_label.config(image=self.tk_img)
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to load image: {e}")
            self.current_index += 1
            self.show_image()

    def label_image(self, label):
        if self.current_index < 0 or self.current_index >= len(self.image_list):
            return
        img_path = self.image_list[self.current_index]
        filename = os.path.basename(img_path)
        label_map = {0: "boat_docked", 1: "no_boats", 2: "too_cloudy"}
        class_dir = label_map[label]
        target_dir = os.path.join(self.train_dir, class_dir)
        target_path = os.path.join(target_dir, filename)

        if os.path.exists(target_path):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(target_dir, f"{base}_{counter}{ext}")):
                counter += 1
            filename = f"{base}_{counter}{ext}"
            target_path = os.path.join(target_dir, filename)

        try:
            shutil.move(img_path, target_path)
        except Exception as e:
            messagebox.showerror("Move Error", f"Failed to move file: {e}")
            return

        relative_path = os.path.join("train", class_dir, filename).replace(os.sep, '/')
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([relative_path, label, "train", False])

        self.history.append({
            'moved_path': target_path,
            'original_path': img_path,
            'filename': filename
        })
        self.undo_btn.config(state=tk.NORMAL)
        self.image_list.pop(self.current_index)
        if self.current_index >= len(self.image_list):
            self.current_index = max(0, len(self.image_list) - 1)
        self.show_image()
        self.update_progress()

    def undo_last(self):
        if not self.history:
            return
        last = self.history.pop()
        try:
            shutil.move(last['moved_path'], last['original_path'])
        except Exception as e:
            messagebox.showerror("Undo Error", f"Failed to undo: {e}")
            return
        try:
            with open(self.csv_path, 'r') as f:
                lines = f.readlines()
            with open(self.csv_path, 'w') as f:
                f.writelines(lines[:-1])
        except Exception as e:
            messagebox.showerror("Undo Error", f"Failed to update CSV: {e}")
        self.image_list.insert(self.current_index, last['original_path'])
        if not self.history:
            self.undo_btn.config(state=tk.DISABLED)
        self.show_image()
        self.update_progress()

    def update_progress(self):
        labeled = len(self.history)
        total = len(self.image_list) + labeled
        self.progress_label.config(text=f"Progress: {labeled} / {total} images labeled")


if __name__ == "__main__":
    root = tk.Tk()
    unlabeled_dir = sys.argv[1] if len(sys.argv) > 1 else None
    app = LabelGUI(root, unlabeled_dir)
    root.mainloop()
