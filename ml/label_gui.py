"""
Dock Boat Image Labeler GUI

Usage:
    python label_gui.py [parent_directory]

Description:
    A Tkinter-based tool to label unlabeled dock satellite images into 3 classes:
    - Boat docked (label 0, key '2' or "Boat" button)
    - No boats (label 1, key '1' or "No Boat" button)
    - Too cloudy (label 2, key '3' or "Too Cloudy" button)

    Labeled images are moved to ml/data/train/{class}/ and entries are automatically
    appended to ml/data/dataset.csv in the format:
    image_path, label, split, is_synthetic

    The tool processes all subdirectories within the provided parent directory.
    For each subdirectory, it looks for a 'png_chips' folder and loads all .png
    images from within that folder for labeling.

Controls:
    - Keyboard: 1 (No Boat), 2 (Boat), 3 (Too Cloudy), Ctrl+Z (Undo last label)
    - GUI Buttons: Click the corresponding class button or "Undo" button

Arguments:
    parent_directory: Optional path to parent folder containing subdirectories.
                       Each subdirectory should have a 'png_chips' folder with .png images.
                       If omitted, a directory chooser dialog will open.
"""

import csv
import glob
import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk


class LabelGUI:
    def __init__(self, root, parent_dir=None):
        self.root = root
        self.root.title("Dock Boat Image Labeler")
        self.root.geometry("1200x1000")

        self.parent_dir = parent_dir
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
            with open(self.csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["image_path", "label", "split", "is_synthetic"])

        self.setup_ui()
        if self.parent_dir:
            self.load_image_list()
        else:
            self.select_directory()

    def setup_ui(self):
        self.progress_label = tk.Label(self.root, text="Progress: 0 / 0 images labeled")
        self.progress_label.pack()

        self.path_label = tk.Label(
            self.root, text="Current: No parent directory selected", wraplength=1000
        )
        self.path_label.pack(pady=5)

        self.canvas = tk.Canvas(self.root, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True, pady=10)
        self.canvas.bind("<Configure>", lambda e: self.display_image())

        self.current_img = None
        self.tk_img = None

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="No Boat (1)", width=15, command=lambda: self.label_image(1)
        ).grid(row=0, column=0, padx=5)
        tk.Button(
            btn_frame, text="Boat (2)", width=15, command=lambda: self.label_image(0)
        ).grid(row=0, column=1, padx=5)
        tk.Button(
            btn_frame,
            text="Too Cloudy (3)",
            width=15,
            command=lambda: self.label_image(2),
        ).grid(row=0, column=2, padx=5)

        self.undo_btn = tk.Button(
            self.root,
            text="Undo (Ctrl+Z)",
            width=30,
            command=self.undo_last,
            state=tk.DISABLED,
        )
        self.undo_btn.pack(pady=5)

        if not self.parent_dir:
            tk.Button(
                self.root, text="Select Parent Directory", command=self.select_directory
            ).pack(pady=5)

        self.root.bind("1", lambda e: self.label_image(1))
        self.root.bind("2", lambda e: self.label_image(0))
        self.root.bind("3", lambda e: self.label_image(2))
        self.root.bind("<Control-z>", lambda e: self.undo_last())

    def select_directory(self):
        self.parent_dir = filedialog.askdirectory(title="Select Parent Directory")
        if self.parent_dir:
            self.load_image_list()
        else:
            messagebox.showwarning("No Directory", "No directory selected.")

    def load_image_list(self):
        self.image_list = []
        try:
            subdirs = [
                d
                for d in os.listdir(self.parent_dir)
                if os.path.isdir(os.path.join(self.parent_dir, d))
            ]
        except Exception as e:
            messagebox.showerror(
                "Directory Error", f"Failed to list subdirectories: {e}"
            )
            return

        for subdir in subdirs:
            png_chips_dir = os.path.join(self.parent_dir, subdir, "png_chips")
            if os.path.isdir(png_chips_dir):
                for ext in ("*.png", "*.PNG"):
                    self.image_list.extend(glob.glob(os.path.join(png_chips_dir, ext)))

        self.image_list = list(set(self.image_list))
        if not self.image_list:
            messagebox.showinfo(
                "No Images", "No .png images found in any png_chips subdirectories."
            )
            return
        self.current_index = 0
        self.show_image()
        self.update_progress()

    def show_image(self):
        if self.current_index < 0 or self.current_index >= len(self.image_list):
            self.canvas.delete("all")
            self.path_label.config(text="No more images to label.")
            return
        img_path = self.image_list[self.current_index]
        self.path_label.config(text=f"Current: {img_path}")
        try:
            self.current_img = Image.open(img_path)
            self.display_image()
        except Exception as e:
            messagebox.showerror("Image Error", f"Failed to load image: {e}")
            self.current_index += 1
            self.show_image()

    def display_image(self):
        if self.current_img is None:
            return
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            self.root.after(50, self.display_image)
            return
        img = self.current_img.copy()
        img_ratio = img.width / img.height
        canvas_ratio = canvas_width / canvas_height
        if img_ratio > canvas_ratio:
            new_width = canvas_width
            new_height = int(canvas_width / img_ratio)
        else:
            new_height = canvas_height
            new_width = int(canvas_height * img_ratio)
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        self.canvas.create_image(x, y, anchor=tk.NW, image=self.tk_img)

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

        relative_path = os.path.join("train", class_dir, filename).replace(os.sep, "/")
        with open(self.csv_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([relative_path, label, "train", False])

        self.history.append(
            {"moved_path": target_path, "original_path": img_path, "filename": filename}
        )
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
            shutil.move(last["moved_path"], last["original_path"])
        except Exception as e:
            messagebox.showerror("Undo Error", f"Failed to undo: {e}")
            return
        try:
            with open(self.csv_path, "r") as f:
                lines = f.readlines()
            with open(self.csv_path, "w") as f:
                f.writelines(lines[:-1])
        except Exception as e:
            messagebox.showerror("Undo Error", f"Failed to update CSV: {e}")
        self.image_list.insert(self.current_index, last["original_path"])
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
    parent_dir = sys.argv[1] if len(sys.argv) > 1 else None
    app = LabelGUI(root, parent_dir)
    root.mainloop()
