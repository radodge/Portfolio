import os
import cv2
from cv2 import cuda
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import pillow_heif
import numpy as np
from screeninfo import get_monitors
from CDT_processing import CornerDetector
from CDT_config import CornerDetectionConfig, test_config, gui_config
from CDT_visualizer import draw_corners, draw_lines


def load_image_as_numpy_array(file_path, processing_config):
    """
    Loads an image file and converts it to a NumPy array.

    Uses OpenCV (cv2.imread) for all formats except HEIC.
    HEIC files are loaded using pillow-heif and converted from RGB to BGR.

    Args:
        file_path (str): Path to the image file.

    Returns:
        np.ndarray: BGR image as a NumPy array, or None if an error occurs.
    """
    try:
        cuda_enabled = processing_config.CUDA_ENABLED
        # HEIC Handling (Uses Pillow-HEIF, but converts from RGB to BGR)
        if file_path.lower().endswith(".heic"):
            heif_image = pillow_heif.open_heif(file_path)
            img = Image.frombytes(heif_image.mode, heif_image.size, heif_image.data) # type: ignore
            img_array = np.array(img)  # This is in RGB format

            # Convert from RGB to BGR to match OpenCV's default format
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        else:
            # Load image using OpenCV (BGR format by default)
            img_array = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

        if img_array is None:
            raise RuntimeError(f"Failed to load {file_path} using OpenCV.")

        # if cuda_enabled:
        #     # If CUDA is enabled, convert the image to a format suitable for GPU processing
        #     gpu_mat = cv2.cuda_GpuMat()
        #     gpu_mat.upload(img_array)
        #     img = gpu_mat
        # else:
        #     img = img_array

        # return img  # Return image in BGR format
        return img_array  # Return image in BGR format

    except Exception as e:
        print(f"Failed to load image file {file_path}: {e}")
        return None

class CornerDetectionGUI:
    def __init__(self, root, test_config, gui_config):
        self.root = root
        self.gui_config = gui_config
        self.root.title(self.gui_config["window_title"])
        self.root.config(bg="#2E2E2E")

        self.monitor_number = self.gui_config.get("monitor_number", 0)

        monitors = get_monitors()
        target_monitor = monitors[self.monitor_number] if len(monitors) > 1 else monitors[0]
        w, h = int(target_monitor.width*0.95), int(target_monitor.height*0.95)
        self.root.geometry(f"{w}x{h}+{target_monitor.x}+{target_monitor.y}")
        self.window_width = w
        self.window_height = h
        self.root.state("zoomed")

        # Processing state
        self.image_paths = []
        self.current_index = 0
        self.current_image = None
        self.full_res_display_image = None
        self.image_tk = None
        self.result = None
        self.response_image = None

        self.gray = None
        self.blurred_gray = None
        self.canny_edges = None
        self.morphed_edges = None
        self.lines = None
        self.filtered_lines = None

        # Core components
        self.config = CornerDetectionConfig()
        self.detector = CornerDetector(self.config)

        self.start_folder = test_config.get("start_folder", os.getcwd())
        self.start_index = test_config.get("start_index", 0)

        

        self.define_styles()
        self.setup_gui()
        self.load_folder(self.start_folder)

        self.magnifier_size = self.gui_config.get("magnifier_size", 150)
        self.magnifier_panel = ttk.Label(self.root)
        self.magnifier_panel.grid(row=0, column=2, padx=10, pady=10, sticky="ne")
        self.magnifier_panel.grid_remove()  # Start hidden

        self.image_label.bind("<Motion>", self.handle_mouse_motion)
        self.image_label.bind("<Leave>", lambda e: self.magnifier_panel.grid_remove())
        self.root.bind("<KeyRelease-Shift_L>", lambda e: self.magnifier_panel.grid_remove())
        self.root.bind("<KeyRelease-Shift_R>", lambda e: self.magnifier_panel.grid_remove())


    def define_styles(self):
        # Global style definition
        self.style = ttk.Style()

        self.gui_styles = {
            "button_width": 16,
            "entry_width": 10,
            "font_name": "Segoe UI",
            "font_size": 18,
            "padding": {"x": 5, "y": 20},
            "dark_1": "#2E2E2E",
            "dark_2": "#1A1A1A",
        }

        self.style.configure(
            'TFrame',
            background="#2E2E2E",
            foreground="white"
        )
        
        self.style.configure(
            'TButton',
            font=(self.gui_styles["font_name"], self.gui_styles["font_size"]),
            background=self.gui_styles["dark_2"],
            foreground="black",
            # padding=(5, 5)
        )
        self.style.configure(
            "Process.TButton",
            font=(self.gui_styles["font_name"], int(1.5*self.gui_styles["font_size"]))
        )

        self.style.configure(
            "TLabel",
            font=(self.gui_styles["font_name"], self.gui_styles["font_size"]),
            # background="#1A1A1A",
            background=self.gui_styles["dark_2"],
            foreground="white"
        )
        self.style.configure(
            "Status.TLabel",
            font=(self.gui_styles["font_name"], int(2.0*self.gui_styles["font_size"]), "bold"),
            background=self.gui_styles["dark_2"],
            foreground="white"
        )
        self.style.configure(
            "Header.TLabel",
            font=(self.gui_styles["font_name"], int(1.25*self.gui_styles["font_size"]), "bold")
        )

        self.style.configure(
            'TLabelframe',
            font=(self.gui_styles["font_name"], self.gui_styles["font_size"]),
            background=self.gui_styles["dark_2"],
            foreground="white",
        )
        self.style.configure(
            'TLabelframe.Label',
            font=(self.gui_styles["font_name"], int(1.25*self.gui_styles["font_size"])),
            background=self.gui_styles["dark_2"],
            foreground="white",
        )
        # self.style.configure("Param_Group.TLabelFrame", font=(self.gui_styles["font_name"], self.gui_styles["font_size"]))

        self.style.configure(
            "TCheckbutton",
            font=(self.gui_styles["font_name"], int(1.25*self.gui_styles["font_size"])),
            background=self.gui_styles["dark_2"],
            foreground="white"
        )
        self.style.configure(
            "Custom.TEntry",
            font=("Arial", self.gui_styles["font_size"])
        )

        self.style.configure(
            "TScale",
            background=self.gui_styles["dark_1"],
        )

    def setup_gui(self):
        # Layout: Left (image), Right (controls), Bottom (buttons)
        self.image_label = ttk.Label(self.root)
        self.image_label.grid(
            row=0,
            column=0,
            sticky="nsw",
            padx=10,
            pady=10
        )

        self.status_label = ttk.Label(self.root, text="Load a folder to begin.", style="Status.TLabel")
        self.status_label.grid(
            row=1,
            column=0,
            sticky="new",
            padx=5,
            pady=5
        )

        self.controls_frame = ttk.Frame(self.root)
        self.controls_frame.grid(
            row=0,
            column=1,
            sticky="nsw",
            padx=10,
            pady=10
        )

        self.load_controls()
        self.load_buttons()
        self.lines_label = ttk.Label(self.controls_frame, text="Waiting for detection", style="Header.TLabel")
        self.lines_label.grid(row=4, column=0, sticky="nsew", padx=5, pady=5)

    def load_controls(self):
        self.param_frames = []
        self.entries = {}

        group_1 = [
            ("Gaussian Blur Parameters", self.config.blur_config),
            ("HoughLinesP() Parameters", self.config.hough_config)
        ]
        self.left_control_frame = ttk.Frame(self.controls_frame, padding=(5, 5))
        self.left_control_frame.grid(row=0, column=0, sticky="nw", padx=15, pady=15)
        
        group_2 = [
            ("Canny Detector Parameters", self.config.canny_config),
            ("Morphological Parameters", self.config.morph_config),
        ]
        self.right_control_frame = ttk.Frame(self.controls_frame, padding=(5, 5))
        self.right_control_frame.grid(row=0, column=1, sticky="nw", padx=15, pady=15)

        kernel_keys = {"kernel_w", "kernel_size", "apertureSize", "morph_kernel_w", "iterations"}

        # Combine both groups with corresponding frames
        param_groups = [
            (group_1, self.left_control_frame),
            (group_2, self.right_control_frame)
        ]

        for group, frame in param_groups:
            frame_row = 0
            for header, param_dict in group:
                header_frame = ttk.LabelFrame(
                    frame,
                    text=header,
                    labelanchor='nw',
                    style="TLabelframe"
                )
                header_frame.grid(
                    row=frame_row,
                    column=0,
                    pady=(20, 5),
                    sticky="w"
                )

                param_row = 0
                for key, value in param_dict.items():
                    # Label
                    ttk.Label(header_frame, text=key).grid(row=param_row, column=0, sticky="w", padx=5)

                    if isinstance(value, bool):
                        var = tk.BooleanVar(value=value)
                        chk = ttk.Checkbutton(header_frame, variable=var)
                        chk.grid(row=param_row, column=1, sticky="w")
                        self.entries[key] = var
                    else:
                        entry = ttk.Entry(header_frame, font=("Arial", self.gui_styles["font_size"]), width=self.gui_styles["entry_width"])
                        entry.insert(0, str(value))
                        entry.grid(row=param_row, column=1, sticky="w")
                        self.entries[key] = entry

                        col = 2
                        if isinstance(value, float):
                            scale = ttk.Scale(
                                header_frame, from_=0.0, to=max(value * 10, 1.0), value=value,
                                orient="horizontal", length=240,
                                command=lambda val, e=entry: e.delete(0, tk.END) or e.insert(0, f"{float(val):.2f}"),

                            )
                            scale.grid(row=param_row, column=col, sticky="w", padx=5)

                        elif key in ("lowThreshold", "highThreshold"):
                            scale = ttk.Scale(
                                header_frame, from_=0, to=max(value * 10, 1), value=value,
                                orient="horizontal", length=240,
                                command=lambda val, e=entry: e.delete(0, tk.END) or e.insert(0, str(round(float(val)))),
                                style="TScale"
                            )
                            scale.grid(row=param_row, column=col, sticky="w", padx=5)

                        elif isinstance(value, int) and key not in kernel_keys:
                            self.major_adjustment = self.gui_config["major_adjustment"]
                            self.minor_adjustment = self.gui_config["minor_adjustment"]
                            def add_buttons(entry, val):
                                btn_frame = ttk.Frame(header_frame, style="TFrame")
                                btn_frame.grid(row=param_row, column=col, sticky="w", padx=2, pady=2, ipadx=2, ipady=2)
                                def adjust(perc):
                                    try:
                                        current = int(entry.get())
                                        factor = perc / 100
                                        delta = int(current * factor)
                                        entry.delete(0, tk.END)
                                        entry.insert(0, str(current + delta))
                                    except:
                                        pass
                                ttk.Button(btn_frame, text="--", width=5, command=lambda: adjust(-self.major_adjustment_var.get())).grid(row=0, column=0)
                                ttk.Button(btn_frame, text="-", width=3, command=lambda: adjust(-self.minor_adjustment_var.get())).grid(row=0, column=1)
                                ttk.Button(btn_frame, text="+", width=3, command=lambda: adjust(+self.minor_adjustment_var.get())).grid(row=0, column=2)
                                ttk.Button(btn_frame, text="++", width=5, command=lambda: adjust(+self.major_adjustment_var.get())).grid(row=0, column=3)

                            add_buttons(entry, value)

                        elif key in kernel_keys:
                            if key == "iterations":
                                def add_buttons(entry, val):
                                    btn_frame = ttk.Frame(header_frame)
                                    btn_frame.grid(row=param_row, column=col, sticky="w", padx=5)
                                    def adjust(val):
                                        try:
                                            current = int(entry.get())
                                            entry.delete(0, tk.END)
                                            entry.insert(0, str(current + val))
                                        except:
                                            pass
                                    ttk.Button(btn_frame, text="-1", width=4, command=lambda: adjust(-1)).grid(row=0, column=0)
                                    ttk.Button(btn_frame, text="+1", width=4, command=lambda: adjust(+1)).grid(row=0, column=1)
                                add_buttons(entry, value)
                            else:
                                def add_buttons(entry, val):
                                    btn_frame = ttk.Frame(header_frame)
                                    btn_frame.grid(row=param_row, column=col, sticky="w", padx=5)
                                    def adjust(val):
                                        try:
                                            current = int(entry.get())
                                            entry.delete(0, tk.END)
                                            entry.insert(0, str(current + val))
                                        except:
                                            pass
                                    ttk.Button(btn_frame, text="-2", width=4, command=lambda: adjust(-2)).grid(row=0, column=0)
                                    ttk.Button(btn_frame, text="+2", width=4, command=lambda: adjust(2)).grid(row=0, column=1)
                                add_buttons(entry, value)

                    param_row += 1
                frame_row += 1

        # Major/Minor Adjustment Entries
        ttk.Label(self.controls_frame, text="Major Adjustment %").grid(row=1, column=0, sticky="w", padx=5)
        self.major_adjustment_var = tk.IntVar(value=self.gui_config["major_adjustment"])
        ttk.Entry(
            self.controls_frame,
            textvariable=self.major_adjustment_var,
            font=("Arial", self.gui_styles["font_size"]),
            width=self.gui_styles["entry_width"]
        ).grid(row=1, column=0, sticky="e", padx=5)

        ttk.Label(self.controls_frame, text="Minor Adjustment %").grid(row=2, column=0, sticky="w", padx=5)
        self.minor_adjustment_var = tk.IntVar(value=self.gui_config["minor_adjustment"])
        ttk.Entry(
            self.controls_frame,
            textvariable=self.minor_adjustment_var,
            font=("Arial", self.gui_styles["font_size"]),
            width=self.gui_styles["entry_width"]
        ).grid(row=2, column=0, sticky="e", padx=5)
        
        # CUDA and Single Photo toggles
        self.use_cuda = tk.BooleanVar(value=self.config.CUDA_ENABLED)
        ttk.Checkbutton(self.controls_frame, text="Use CUDA", variable=self.use_cuda).grid(row=3, column=0, sticky="w", pady=5)

        self.single_photo = tk.BooleanVar(value=self.config.SINGLE_PHOTO)
        ttk.Checkbutton(self.controls_frame, text="Single Photo", variable=self.single_photo).grid(row=3, column=0, sticky="e", pady=5)

    def load_buttons(self):
        button_frame = ttk.Frame(self.controls_frame)
        button_frame.grid(
            row=5,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10
        )

        button_row = 0
        ttk.Button(button_frame, text="Detect Lines", command=self.detect_lines, style="Process.TButton"
                ).grid(
                    row=button_row,
                    column=0,
                    columnspan=3,
                    sticky="nsew",
                    pady=20
                )
                
        button_row += 1
        ttk.Button(button_frame, text="Show Canny", command=self.show_canny_edges, style="Process.TButton"
            ).grid(
                row=button_row,
                column=0,
                columnspan=3,
                sticky="nsew",
                pady=10
            )
        
        button_row += 1
        ttk.Button(button_frame, text="Show Blurred", command=self.show_blurred_image
            ).grid(
                row=button_row,
                column=0,
                padx=5,
                pady=5
            )
        ttk.Button(button_frame, text="Restore Defaults", command=self.restore_defaults
            ).grid(
                row=button_row,
                column=2,
                padx=5,
                pady=5
            )
        
        button_row += 1
        ttk.Button(button_frame, text="Prev", command=self.prev_image).grid(row=button_row, column=0, padx=5, pady=15)
        ttk.Button(button_frame, text="Load Folder", command=self.load_folder).grid(row=button_row, column=1, padx=5, pady=15)
        ttk.Button(button_frame, text="Next", command=self.next_image).grid(row=button_row, column=2, padx=5, pady=15)
        # ttk.Button(button_frame, text="Process", command=self.process_current_image).grid(row=0, column=3)

    def load_folder(self, path=None):
        folder = path or filedialog.askdirectory(initialdir=self.start_folder)
        if folder:
            exts = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".heic", ".heif")
            self.image_paths = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith(exts)
            ]
            self.image_paths.sort()
            self.current_index = min(self.start_index, len(self.image_paths) - 1) if self.image_paths else 0
            self.load_image()

    def load_image(self):
        if not self.image_paths:
            return
        path = self.image_paths[self.current_index]
        self.current_image = load_image_as_numpy_array(path, self.config)
        self.display_image(self.current_image)
        self.status_label.config(text=f"Loaded: {os.path.basename(path)}")

    def display_image(self, image):
        """
        Resizes the image based on a fraction of the screen dimensions while preserving aspect ratio.
        """
        if image is None:
            return
        
        if isinstance(image, cuda.GpuMat):
            cpu_image = image.download()
        else:
            cpu_image = image

        self.full_res_display_image = cpu_image.copy()

        # Get target screen size
        max_width = int(self.window_width * 0.80)
        max_height = int(self.window_height * 0.90)

        # Convert image and get original dimensions
        image_rgb = cv2.cvtColor(cpu_image, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        orig_width, orig_height = image_pil.size

        # Compute scaling factor to fit within target bounds
        scale = min(max_width / orig_width, max_height / orig_height)
        self.display_scale = scale
        new_size = (int(orig_width * scale), int(orig_height * scale))

        # Resize and display
        resized_image = image_pil.resize(new_size, Image.Resampling.LANCZOS)
        self.image_tk = ImageTk.PhotoImage(resized_image)
        self.image_label.configure(image=self.image_tk)
        # self.image_label.image = self.image_tk

    def handle_mouse_motion(self, event):
        if not (event.state & 0x0001):  # Only proceed if Shift is held
            self.magnifier_panel.grid_remove()
            return

        if self.full_res_display_image is None:
            return

        scale = self.display_scale
        x_full = int(event.x / scale)
        y_full = int(event.y / scale)
        n = self.magnifier_size
        h, w = self.full_res_display_image.shape[:2]

        half = n // 2
        x1 = max(0, x_full - half)
        y1 = max(0, y_full - half)
        x2 = min(w, x_full + half)
        y2 = min(h, y_full + half)

        cropped = self.full_res_display_image[y1:y2, x1:x2]

        # Pad if near border
        padded = np.zeros((n, n, 3), dtype=np.uint8)
        padded[:y2 - y1, :x2 - x1] = cropped

        zoom_image = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        zoom_pil = Image.fromarray(zoom_image).resize((n*2, n*2), Image.Resampling.NEAREST)
        self.zoom_tk = ImageTk.PhotoImage(zoom_pil)
        self.magnifier_panel.configure(image=self.zoom_tk)
        self.magnifier_panel.grid()

    def update_config(self):
        # self.config.CUDA_ENABLED = self.use_cuda
        # self.config.CUDA_ENABLED = self.use_cuda.get()
        # self.config.SINGLE_PHOTO = self.single_photo

        # Update nested config dictionaries from UI entries
        for key, widget in self.entries.items():
            # Get correct config target (blur or GFTT)
            if key in self.config.blur_config:
                config_dict = self.config.blur_config

            elif key in self.config.canny_config:
                config_dict = self.config.canny_config

            elif key in self.config.morph_config:
                config_dict = self.config.morph_config
                print(f"[update_config] Morph config: {config_dict}")

            elif key in self.config.hough_config:
                config_dict = self.config.hough_config

            else:
                continue  # Skip unknown keys

            # Extract the value from the widget
            if isinstance(widget, tk.BooleanVar):
                config_dict[key] = widget.get()
            else:
                current_type = type(config_dict[key])
                try:
                    config_dict[key] = current_type(widget.get())
                except ValueError:
                    print(f"[WARN] Invalid entry for '{key}': {widget.get()} — keeping previous value.")

        self.detector.reconfigure(self.config)

    def detect_lines(self):
        if self.current_image is None:
            return
        self.update_config()
        self.prev_num_lines = len(self.filtered_lines) if self.filtered_lines is not None else 0
        self.gray = self.detector.convert_to_grayscale(self.current_image)
        self.blurred_gray = self.detector.apply_blur(self.gray)
        self.canny_edges = self.detector.apply_canny(self.blurred_gray)
        self.morphed_edges = self.detector.apply_morphology(self.canny_edges)
        self.lines = self.detector.detect_lines(self.morphed_edges)
        self.filtered_lines = self.detector.filter_lines(self.lines)
        # self.result = draw_lines(self.current_image, self.filtered_lines)
        self.result = draw_lines(self.morphed_edges, self.filtered_lines)
        # cv2.imwrite("Lines.jpg", self.result)
        self.display_image(self.result)
        self.lines_label.config(text=f"{len(self.filtered_lines)} lines detected. Prev: {self.prev_num_lines}")
        
    def show_blurred_image(self):
        if self.blurred_gray is None:
            return
        self.display_image(self.blurred_gray)
        self.status_label.config(text="Blurred image displayed.")

    def show_canny_edges(self):
        self.update_config()
        self.gray = self.detector.convert_to_grayscale(self.current_image)
        self.blurred_gray = self.detector.apply_blur(self.gray)
        self.canny_edges = self.detector.apply_canny(self.blurred_gray)
            
        self.display_image(self.canny_edges)
        self.status_label.config(text="Canny edges displayed.")

    def show_morphed_edges(self):
        if self.morphed_edges is None:
            return
        self.display_image(self.morphed_edges)
        self.status_label.config(text="Morphed edges displayed.")

    def next_image(self):
        if self.image_paths and self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_image()

    def prev_image(self):
        if self.image_paths and self.current_index > 0:
            self.current_index -= 1
            self.load_image()

    def restore_defaults(self):
        # Replace the config object
        self.config = CornerDetectionConfig()

        # Update CUDA/SINGLE_PHOTO toggles
        self.use_cuda.set(self.config.CUDA_ENABLED)
        self.single_photo.set(self.config.SINGLE_PHOTO)

        # Update major/minor adjustment entries
        self.major_adjustment_var.set(self.gui_config["major_adjustment"])
        self.minor_adjustment_var.set(self.gui_config["minor_adjustment"])

        # Update all entry/checkbutton widgets
        for key, widget in self.entries.items():
            if key in self.config.blur_config:
                value = self.config.blur_config[key]
            elif key in self.config.canny_config:
                value = self.config.canny_config[key]
            elif key in self.config.morph_config:
                value = self.config.morph_config[key]
            elif key in self.config.hough_config:
                value = self.config.hough_config[key]
            else:
                continue  # Skip unknown keys

            if isinstance(widget, tk.BooleanVar):
                widget.set(bool(value))
            else:
                widget.delete(0, tk.END)
                widget.insert(0, str(value))

        # Reconfigure the detector
        self.detector.reconfigure(self.config)

        # Optionally update the status label
        self.status_label.config(text="Restored default configuration.")

        if self.current_image is not None:
            self.detect_lines()

def main():
    root = tk.Tk()
    app = CornerDetectionGUI(root, test_config, gui_config)
    print(f"[INFO] Starting GUI with folder: {test_config['start_folder']}")
    print(f"[INFO] Starting GUI with index: {test_config['start_index']}")

    app.root.mainloop()

if __name__ == "__main__":
    main()
