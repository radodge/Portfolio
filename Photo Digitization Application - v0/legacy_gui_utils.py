from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from tkinter import font
from PIL import Image, ImageTk
import cv2
import numpy as np
import platform
import math
import threading
from datetime import datetime
import shutil
import os
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

class ImageEditorGUI:
    def __init__(self, gui_config, subphoto_saving_queue, stop_event):
        """
        Initialize the ImageEditorGUI with the provided configuration.

        Args:
            config (dict): A dictionary of GUI configuration settings:
        """
        # Step 1: Parse configuration and set instance variables
        self.bg_color_1 = gui_config.get("Background_Color_1", "darkgray")
        self.bg_color_2 = gui_config.get("Background_Color_2", "gray")
        self.default_window_size = gui_config.get("Default_Window_Size", "1200x800+100+100")
        self.display_mode = gui_config.get("Display_Mode", "None")
        self.debug_mode = gui_config.get("Debug_Mode", False)

        # if sys.platform == "win32":
        #     try:
        #         # Force the highest available DPI awareness mode
        #         ctypes.windll.user32.SetProcessDPIAware()  # Works on older Windows versions
        #         ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI awareness
        #     except Exception as e:
        #         print(f"Could not set DPI awareness: {e}")

        self.root = Tk()  # Use Tk for the main application window
        self.root.title("Photo Processing")

        # self.scaling_factor = None
        self.scaling_factor = 1
        self.get_display_scaling()

        if self.debug_mode:
            print(f"DPI Scaling Factor: {self.scaling_factor}")

        self.root.minsize(800, 600)    # Minimum window size

        # Base font size (default UI font size)
        self.base_font_size = 16  # Adjust as needed
        self.default_font = "Arial"
        self.text_color = 'white'

        self.root.option_add('*tearOff', FALSE)

        self.menu_bar = Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.root.update_idletasks()
        # Store screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        # self.screen_width = int(self.root.winfo_screenwidth() * self.scaling_factor)
        # self.screen_height = int(self.root.winfo_screenheight() * self.scaling_factor)

        self.single_subphoto_wscale = 0.95
        self.single_subphoto_hscale = 0.95

        self.multi_subphoto_wscale = 0.95
        self.multi_subphoto_hscale = 0.95

        self.combined_photo = None
        self.adjusted_photo = None  # Modifiable version of the subphoto
        self.base_name = None
        self.part_number = None

        self.scaled_combined_image = None
        self.tk_scaled_combined_image = None
        self.combined_image_label = None

        self.left_frame_width = None

        self.tk_scaled_subphoto = None

        self.subphoto_processing_complete = False # Flag to track if subphoto processing is complete
        self.photo_discarded = False  # Flag to track if the photo was discarded

        self.confirmation_variable = StringVar(value="")  # Default to empty (waiting for user input)
        
        self.save_queue = subphoto_saving_queue
        self.stop_event = stop_event

        self.last_mmdd = "0101"
        self.last_year = "2000"
        self.last_description = ""
        self.description_history = set()  # All unique descriptions

        # Set window geometry based on the Display_Mode
        self.set_display_mode()

        self.define_styles()

        self.create_menu_bar()

        # Create main frames
        self.create_frames()

        self.create_hotkeys()

        # if self.debug_mode:
        #     print(f"\nMain frame grid info: {self.main_frame.grid_info()}\n")
        #     print(f"\nStatus bar grid info: {self.status_bar.grid_info()}\n")
        #     print(f"\nPreview frame grid info: {self.preview_frame.grid_info()}\n")
        #     print(f"\nCombined photo frame grid info: {self.combined_photo_frame.grid_info()}\n")
        #     print(f"\nSubphoto processing frame grid info: {self.subphoto_processing_frame.grid_info()}\n")
        #     print(f"\nTop right frame grid info: {self.top_right_frame.grid_info()}\n")
        #     print(f"\nSubphoto preview frame grid info: {self.subphoto_preview_frame.grid_info()}\n")
        #     print(f"\nPrimary user input frame grid info: {self.primary_user_input_frame.grid_info()}\n")

        self.root.update_idletasks()

    def define_styles(self):
        """Define custom styles for ttk widgets, ensuring DPI-aware font scaling."""
        
        # # Base font size (default UI font size)
        # self.base_font_size = 16  # Adjust as needed
        # self.default_font = "Arial"
        # self.text_color = 'white'

        # Dynamically adjust fonts based on DPI scaling factor
        self.scaled_font_size = int(self.base_font_size * self.scaling_factor)
        # self.scaled_font_size = int(self.base_font_size * self.scaling_factor)

        # Centralized font dictionary (avoids repetition)
        self.fonts = {
            "label": (self.default_font, self.scaled_font_size),
            "frame_label": (self.default_font, int(self.scaled_font_size * 0.8)),
            "entry": (self.default_font, int(self.scaled_font_size * 1.2)),
            "combobox": (self.default_font, int(self.scaled_font_size * 1.2)),
            "button": (self.default_font, int(self.scaled_font_size * 1.2)),  # Slightly larger for buttons
            "confirm_button": (self.default_font, int(self.scaled_font_size * 1.5), "bold"),
            "quit_button": (self.default_font, int(self.scaled_font_size * 1.0), "bold")
        }

        # Apply the font settings globally for widgets
        self.root.option_add("*Font", f"{self.default_font} {self.scaled_font_size}")

        # Define styles
        self.style = ttk.Style()

        # General frame style
        self.style.configure(
            'TFrame',
            background=self.bg_color_1,
            borderwidth=2,
            relief='solid'
            )
        
        # self.style.configure(
        #     'Subphoto_Processing_Frame.TFrame',
        #     background=self.bg_color_1,
        #     padding=10
        #     )
        
        # Style for Label Frames (Borders and Padding)
        self.style.configure(
            'TLabelframe',
            background=self.bg_color_1,
            foreground=self.text_color,
            # font=self.fonts["label"],
            borderwidth=2,
            relief='groove',
            # padding=10  # Add some padding inside the frame
        )
        # Customize the title label of LabelFrames
        self.style.configure(
            'TLabelframe.Label',
            font=self.fonts["frame_label"],
            foreground=self.text_color,
            background=self.bg_color_1,
            padding=5
        )

        # Custom frame styles
        self.style.configure(
            'Combined_Photo.TLabelframe',
            padding=10,
            background=self.bg_color_1,
            relief='raised'
            )
        self.style.configure(
            'Subphoto_Preview_Window.TLabelframe',
            padding=10,
            background=self.bg_color_1,
            relief='solid'
            )
        self.style.configure(
            'M_Subphoto_Preview.TLabelframe',
            # padding=5,
            background=self.bg_color_1,
            relief='solid'
            )

        # Styles for different widgets using centralized fonts
        self.style.configure(
            'TLabel',
            background=self.bg_color_1,
            foreground=self.text_color,
            font=self.fonts["label"]
            )
        self.style.configure(
            'Combined_Photo.TLabel',
            background='black',
            )
        self.style.configure(
            'Subphoto.TLabel',
            background='black',
            )
        
        self.style.configure(
            'TEntry',
            background='white',
            foreground='black',
            font=self.fonts["entry"]
            )
        
        self.style.configure(
            'TCombobox',
            background='white',
            foreground='black',
            # padding=(10, 5, 30, 5),  # Increase right padding for the arrow button
            font=self.fonts["combobox"]
            )
        
        # Button styles
        self.style.configure(
            'TButton',
            font=self.fonts["button"],
            padding=5
            )
        self.style.map(
            'TButton',
            background=[("active", "#777777")]
            )
        # Special buttons
        self.style.configure(
            'Confirm.TButton',
            background='green',
            foreground='black',
            padx=5,
            pady=5,
            font=self.fonts["confirm_button"]
            )
        self.style.configure(
            'Quit.TButton',
            background='red',
            foreground='black',
            padx=5,
            pady=5,
            font=self.fonts["quit_button"]
            )

        if self.debug_mode:
            print(f"Fonts Applied: {self.fonts}")

    def set_display_mode(self):
        """Set the window geometry based on the Display_Mode configuration."""
        if self.display_mode == "fullscreen":
            self.root.attributes("-fullscreen", True)
        elif self.display_mode == "windowed_fullscreen":
            # Cross-platform windowed fullscreen: maximize the window using screen dimensions
            if platform.system() == "Darwin":  # macOS
                # Subtract the height of the dock and menu bar
                self.screen_height -= int(50 * self.scaling_factor)  # Adjust as needed based on your setup
                y_position_offset = int(50 * self.scaling_factor)
                self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+{y_position_offset}")
            else:
                # On Windows/Linux, set the state to "zoomed" to maximize the window
                self.root.state("zoomed")
        
        else:  # Default mode, use specified window size
            self.root.geometry(self.default_window_size)

        self.root.update_idletasks()
        if self.debug_mode:
            print(f"Reported Screen Width: {self.screen_width}")
            print(f"Reported Screen Height: {self.screen_height}")
            print(f"Root Window Width: {self.root.winfo_width()}")
            print(f"Root Window Height: {self.root.winfo_height()}")
    
    def create_menu_bar(self):
        """Create the menu bar with options for the user."""

        # self.menu_bar.configure(bg=self.bg_color_2)
        # self.menu_bar.configure(activebackground=self.bg_color_2)

        # Debug Menu (only if Debug Mode is enabled)
        if self.debug_mode:
            debug_menu = Menu(self.menu_bar, tearoff=0)
            self.menu_bar.add_cascade(label="Debug", menu=debug_menu)

            # Simulate Ingest File (Cascaded Menu)
            simulate_menu = Menu(debug_menu, tearoff=0)
            debug_menu.add_cascade(label="Simulate Ingest File", menu=simulate_menu)

            # Option 1: Choose File Manually
            simulate_menu.add_command(label="Choose File...", command=self.choose_file_dialog)

            # Divider for clarity
            simulate_menu.add_separator()

            # Option 2: Predefined Test Files
            test_files = ["TEST_SCAN_0.tif", "TEST_SCAN_1.tif", "TEST_SCAN_2.tif"]
            for test_file in test_files:
                simulate_menu.add_command(
                    label=test_file,
                    command=lambda file=test_file: self.simulate_ingest_file(file)
                )
                
            debug_menu.add_separator()

            debug_menu.add_command(label="Display Matlab Plot", command=self.display_debug_plot)

            # Bind hotkeys for simulating ingest files
            self.root.bind("0", lambda event: self.simulate_ingest_file("TEST_SCAN_0.tif"))
            self.root.bind("1", lambda event: self.simulate_ingest_file("TEST_SCAN_1.tif"))
            self.root.bind("2", lambda event: self.simulate_ingest_file("TEST_SCAN_2.tif"))

            # geometry_menu = Menu(debug_menu, tearoff=0)
            # debug_menu.add_cascade(label="Change GUI Geometry", menu=geometry_menu)
            # geometry_menu.add_separator()
            # geometry_menu.add_command(label="")

        # File Menu
        file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        # file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Reload Combined Photo", command=self.load_combined_image)
        file_menu.add_command(label="Reload Subphoto", command=self.load_subphoto)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit_app)

        # Edit Menu
        edit_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Rotate Right", command=self.rotate_right)
        edit_menu.add_command(label="Rotate Left", command=self.rotate_left)
        edit_menu.add_command(label="Flip Vertical", command=self.flip_vertical)
        edit_menu.add_command(label="Flip Horizontal", command=self.flip_horizontal)
        edit_menu.add_command(label="Reduce Noise", command=self.reduce_noise)
        edit_menu.add_command(label="CUDA Reduce Noise", command=self.cuda_reduce_noise)
        edit_menu.add_separator()

        style_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Style", menu=style_menu)
        style_menu.add_command(label="Font Settings", command=self.change_font)
        style_menu.add_command(label="Photo Display Scaling", command=self.change_photo_scaling)

        # Help Menu
        help_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        # help_menu.add_command(label="About", command=self.show_about_dialog)

    def create_hotkeys(self):
        """
        Binds hotkeys for quick photo manipulation.
        """
        # Bind the arrow keys to the corresponding functions
        self.root.bind("<Right>", lambda event: self.rotate_right())
        self.root.bind("<Left>", lambda event: self.rotate_left())
        self.root.bind("<Up>", lambda event: self.flip_vertical())
        self.root.bind("<Down>", lambda event: self.flip_horizontal())

        if self.debug_mode:
            # Bind additional keys for other functionalities if needed
            self.root.bind("0", lambda event: self.simulate_ingest_file("TEST_SCAN_0.tif"))
            self.root.bind("1", lambda event: self.simulate_ingest_file("TEST_SCAN_1.tif"))
    
    def create_frames(self):
        """Create and organize the main frames of the GUI."""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main frame for the entire window
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(
            column=0,
            row=0,
            sticky="nsew"
            )
        
        self.main_frame.rowconfigure(0, weight=1)  # Preview frame
        self.main_frame.rowconfigure(1, minsize=(self.root.winfo_height() // 36))  # Status bar
        self.main_frame.columnconfigure(0, weight=1)  # Entire main frame

        # Preview/Editing Section (Top)
        self.preview_frame = ttk.Frame(self.main_frame, style='TFrame')
        self.preview_frame.grid(
            row=0,
            column=0,
            sticky="nsew"
            )
        
        # Status Bar (Bottom Ribbon)
        self.status_bar = ttk.Frame(self.main_frame, style='TFrame')
        self.status_bar.grid(
            row=1,
            column=0,
            sticky=(N, S, E, W)
            )

        self.create_status_bar_children()
        self.create_preview_frame_children()

    def create_status_bar_children(self):
        self.status_bar.rowconfigure(0, weight=1)
        self.status_bar.columnconfigure(0, weight=1)
        # Example status bar with a label
        self.status_label = ttk.Label(self.status_bar, text="Status: Ready", style='TLabel')
        self.status_label.grid(
            row=0,
            column=0,
            padx=10,
            sticky="w"
        )

    def create_preview_frame_children(self):
        self.preview_frame.rowconfigure(0, weight=1)
        self.preview_frame.columnconfigure(1, weight=1)

        # Combined Photo Frame (Left)
        self.combined_photo_frame = ttk.LabelFrame(
            self.preview_frame,
            text="Scanned Photo",
            labelanchor='n',
            style='Combined_Photo.TLabelframe'
            )
        self.combined_photo_frame.grid(
            row=0,
            column=0,
            sticky=(N, S, W)
            )
        self.combined_photo_frame.columnconfigure(0, weight=1)
        self.combined_photo_frame.rowconfigure(0, weight=1)
        
        # Right Frame for Subphoto and Controls
        self.subphoto_processing_frame = ttk.Frame(self.preview_frame, style='TFrame')
        self.subphoto_processing_frame.grid(
            row=0,
            column=1,
            sticky=(N, S, E, W)
            )
        self.subphoto_processing_frame.columnconfigure(0, weight=1)
        # self.subphoto_processing_frame.rowconfigure(0, weight=1)
        self.subphoto_processing_frame.rowconfigure(0, minsize=self.preview_frame.winfo_height()//12)
        # self.subphoto_processing_frame.rowconfigure(0, minsize=int(self.preview_frame.winfo_height()*self.scaling_factor)//12)
        self.subphoto_processing_frame.rowconfigure(1, weight=1)
        # self.subphoto_processing_frame.rowconfigure(2, weight=1)
        self.subphoto_processing_frame.rowconfigure(2, minsize=self.preview_frame.winfo_height()//4)
        # self.subphoto_processing_frame.rowconfigure(2, minsize=int(self.preview_frame.winfo_height()*self.scaling_factor)//4)

        self.create_subphoto_processing_frame_children()

    def create_subphoto_processing_frame_children(self):
        """Create child frames for the right column."""
        # Top child frame (1/16th height)
        self.top_right_frame = ttk.Frame(self.subphoto_processing_frame, style="TFrame")
        self.top_right_frame.grid(
            row=0,
            column=0,
            sticky=(N, E, W)
            )
        self.top_right_frame.rowconfigure(0, weight=1)
        self.top_right_frame.columnconfigure(0, weight=1)
        self.top_right_frame.columnconfigure(1, weight=1)
        
        # Middle child frame (3/4ths height)
        self.subphoto_preview_frame = ttk.LabelFrame(
            self.subphoto_processing_frame,
            text="Subphoto Preview",
            style="Subphoto_Preview_Window.TLabelframe",
            labelanchor='nw'
        )
        self.subphoto_preview_frame.grid(
            row=1,
            column=0,
            padx=10,
            pady=10,
            sticky=(N, S, E, W)
            )
        self.subphoto_preview_frame.rowconfigure(0, weight=1)
        self.subphoto_preview_frame.columnconfigure(0, weight=1)

        # Bottom child frame (3/16ths height)
        self.primary_user_input_frame = ttk.Frame(self.subphoto_processing_frame, style='TFrame')
        self.primary_user_input_frame.grid(
            row=2,
            column=0,
            sticky=(S, E, W)
            )
        self.primary_user_input_frame.rowconfigure(0, weight=1)
        self.primary_user_input_frame.columnconfigure(0, weight=1)
        self.primary_user_input_frame.columnconfigure(1, weight=1)

        # Add widgets to the child frames
        self.populate_right_frames()

    def populate_right_frames(self):
        """Add widgets and layout to the right frames."""
        # Top Right Frame: Base name, subpart label, quit button
        self.base_name_label = ttk.Label(
            self.top_right_frame,
            text="Base Name: None",
            style="TLabel"
        )
        self.base_name_label.grid(
            row=0,
            column=0,
            padx=5,
            # sticky=(N, S, W)
            sticky=(W)
            )

        self.quit_button = ttk.Button(
            self.top_right_frame,
            text="Quit",
            command=self.quit_app,
            style="Quit.TButton"
        )
        self.quit_button.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            # sticky=(N, S, E)
            sticky=(E)
            )

        self.indicate_waiting_for_photos()

        self.load_preview_inputs()

    def load_preview_inputs(self):
        """
        Loads input buttons for the preview stage directly into primary_user_input_frame.

        Args:
            error_message (str, optional): Error message to display within the Discard & Reprocess button.
        """

        # self.subphoto_processing_frame.rowconfigure(2, minsize=self.preview_frame.winfo_height()//4)

        # Clear existing inputs
        for widget in self.primary_user_input_frame.winfo_children():
            widget.destroy()

        self.primary_user_input_frame.columnconfigure(0, weight=1)
        self.primary_user_input_frame.columnconfigure(1, weight=1)

        # Discard & Reprocess Button (With Error Message if present)
        discard_text = "Discard & Reprocess"
        if self.combined_photo != None and self.combined_photo.error_message:
            discard_text += f"\n\n{self.combined_photo.error_message}"  # Smaller text below

        discard_button = ttk.Button(
            self.primary_user_input_frame,
            text=discard_text,
            command=self.discard_and_reprocess,
            style='TButton'
        )
        discard_button.grid(
            row=0,
            column=0,
            padx=5,
            pady=5,
            sticky=(N, S, E, W)
            )

        # Confirm Button (Focused)
        confirm_button = ttk.Button(
            self.primary_user_input_frame,
            text="Confirm & Proceed",
            command=self.confirm_and_process_subphotos,
            style='Confirm.TButton'
        )
        confirm_button.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky=(N, S, E, W)
            )
        
        if self.combined_photo == None:
            confirm_button.state(['disabled'])  # Disable confirm button initially
            discard_button.state(['disabled'])  # Disable discard button initially
        else:
            confirm_button.focus_set()  # Set focus on confirm button

        self.primary_user_input_frame.update_idletasks()

    def scale_combined_image(self, combined_image):
        """
        Scales the given NumPy image while maintaining its aspect ratio,
        considering the preview_frame's padding dynamically.

        Args:
            combined_image (ndarray): The NumPy array representing the image (BGR format).

        Returns:
            ndarray: The resized NumPy image.
        """
        # Update the idle tasks to ensure the latest size values are captured
        self.preview_frame.update_idletasks()

        # Retrieve padding dynamically if set using the 'padding' property of ttk.Frame
        # This ensures that the maximum width and height consider the padding space.
        # padding_value = self.preview_frame.cget("padding")
        # if self.debug_mode:
        #     print(f"Padding Value: {padding_value}")

        # padding = int(str(padding_value[0]))  # Extract left padding

        # Apply inverse DPI scaling factor to ensure correct dimensions
        # scaling_correction = 1 / self.scaling_factor

        # # Get logical (Tkinter) dimensions
        # max_width = int(self.preview_frame.winfo_width() * scaling_correction) #- (2 * padding)
        max_height = int(self.preview_frame.winfo_height() * 0.95) #- (2 * padding)
        # Calculate the maximum allowed width and height by subtracting padding from the frame dimensions
        max_width = int(self.preview_frame.winfo_width() * 0.5)
        # max_height = self.preview_frame.winfo_height() - (2 * padding)

        # Extract the original dimensions of the image
        original_height, original_width = combined_image.shape[:2]

        # Compute the aspect ratio to ensure the image scales uniformly
        aspect_ratio = original_width / original_height

        # Resize the image only if it exceeds the maximum allowable dimensions
        if original_width > max_width or original_height > max_height:
            if aspect_ratio > 1:
                # Image is wider than tall: limit by width
                new_width = max_width
                new_height = int(new_width / aspect_ratio)
            else:
                # Image is taller than wide: limit by height
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
        else:
            # If the image is smaller than the allowed space, keep the original size
            new_width, new_height = original_width, original_height

        self.left_frame_width = int(new_width * 1.05)

        # Resize the image using OpenCV’s INTER_AREA interpolation for high-quality downscaling
        return cv2.resize(combined_image, (new_width, new_height), interpolation=cv2.INTER_AREA)

    def scale_subphoto(self, subphoto, max_width, max_height):
        """
        Scales a subphoto while maintaining its aspect ratio to fit within the given dimensions.

        Args:
            subphoto (ndarray): The subphoto image (BGR format).
            max_width (int): Maximum allowed width.
            max_height (int): Maximum allowed height.

        Returns:
            ndarray: Resized subphoto with preserved aspect ratio.
        """
        h, w = subphoto.shape[:2]
        subphoto_aspect_ratio = w / h
        slot_aspect_ratio = max_width / max_height

        # Determine new size while maintaining aspect ratio
        if w > max_width or h > max_height:
            if subphoto_aspect_ratio < slot_aspect_ratio:   # Subphoto is NARROWER than its destination
                # Limited by height
                new_height = int(max_height * self.single_subphoto_hscale) # ~0.99
                new_width = int(new_height * subphoto_aspect_ratio)
            else:   # Subphoto is WIDER than its target destination
                # Limited by width
                new_width = int(max_width * self.single_subphoto_wscale) # ~0.99
                new_height = int(new_width / subphoto_aspect_ratio)
        else:
            new_width, new_height = w, h  # No scaling needed

        # Resize the subphoto while maintaining aspect ratio
        return cv2.resize(subphoto, (new_width, new_height), interpolation=cv2.INTER_AREA)

    def load_combined_image(self):
        """
        Loads and displays the given combined photo in the GUI.

        Dynamically adjusts the grid weights based on the image width,
        ensuring the right frame scales smoothly.
        """
        # Step 1: Clear previous widgets
        for widget in self.combined_photo_frame.winfo_children():
            widget.destroy()

        # Step 2: Scale the image while maintaining aspect ratio
        self.scaled_combined_image = self.scale_combined_image(self.combined_photo.combined_image)

        # Step 3: Convert to Tkinter-compatible format (BGR -> RGB)
        self.tk_scaled_combined_image = ImageTk.PhotoImage(
            Image.fromarray(cv2.cvtColor(self.scaled_combined_image, cv2.COLOR_BGR2RGB))
        )

        self.preview_frame.columnconfigure(0, minsize=self.left_frame_width)

        # Step 8: Display the image in the frame
        self.combined_image_label = ttk.Label(
            self.combined_photo_frame,
            image=self.tk_scaled_combined_image,
            style='Combined_Photo.TLabel'
            )
        self.combined_image_label.grid(
            row=0,
            column=0,
            sticky=(N, S, E, W)
        )

        # Update status
        self.status_label.config(text="Status: Image Loaded")

        # Step 9: Force GUI update to reflect changes
        self.combined_photo_frame.update_idletasks()
        # self.root.update_idletasks()

    def compute_grid_layout(self, num_subphotos):
        """
        Computes the optimal number of rows and columns to fit the subphotos within subphoto_preview_frame.

        Args:
            num_subphotos (int): Total number of subphotos.

        Returns:
            tuple: (rows, columns)
        """
        if num_subphotos <= 1:
            return (1, 1)  # Single subphoto, no grid needed

        if num_subphotos == 3:
            return (2, 2)

        # Ensure the frame dimensions are updated before measuring
        self.preview_frame.update_idletasks()
        frame_width = self.subphoto_preview_frame.winfo_width()
        frame_height = self.subphoto_preview_frame.winfo_height()

        # Avoid division by zero
        if frame_height == 0:
            frame_aspect_ratio = 1
        else:
            frame_aspect_ratio = frame_width / frame_height

        # **Estimate the initial number of rows and columns**
        sqrt_n = math.sqrt(num_subphotos)

        # Base estimates
        estimated_rows = round(sqrt_n / frame_aspect_ratio)
        estimated_columns = round(sqrt_n * frame_aspect_ratio)

        # Ensure at least 1 row/column
        estimated_rows = max(1, estimated_rows)
        estimated_columns = max(1, estimated_columns)

        # **Refine the layout**
        while estimated_rows * estimated_columns < num_subphotos:
            if estimated_columns <= estimated_rows:
                estimated_columns += 1
            else:
                estimated_rows += 1

        return (estimated_rows, estimated_columns)

    def preview_all_subphotos(self, combined_photo):
        """
        Displays all subphotos in a grid layout inside subphoto_preview_frame for quick user review.

        Args:
            combined_photo (Combined_Photo): The combined photo group to process.
        """
        # if self.debug_mode:
        #     print("\nCheckpoint A: preview_all_subphotos")
        #     print(f"Preview Frame Geometry: {self.preview_frame.winfo_geometry()}")
        #     print(f"Combined Photo Frame Geometry: {self.combined_photo_frame.winfo_geometry()}")
        #     print(f"Subphoto Processing Frame Geometry: {self.subphoto_processing_frame.winfo_geometry()}")
        #     print(f"Top Right Frame Geometry: {self.top_right_frame.winfo_geometry()}")
        #     print(f"Subphoto Preview Frame Geometry: {self.subphoto_preview_frame.winfo_geometry()}")
        #     print(f"Primary User Input Frame Geometry: {self.primary_user_input_frame.winfo_geometry()}\n")

        if combined_photo is not None:
            self.combined_photo = combined_photo
            self.base_name = self.combined_photo.base_name
            self.load_combined_image()
            self.preview_frame.update_idletasks()
            self.subphoto_processing_frame.update_idletasks()
            self.load_preview_inputs()

        # if self.debug_mode:
        #     print("\nCheckpoint B: preview_all_subphotos")
        #     print(f"Preview Frame Geometry: {self.preview_frame.winfo_geometry()}")
        #     print(f"Combined Photo Frame Geometry: {self.combined_photo_frame.winfo_geometry()}")
        #     print(f"Subphoto Processing Frame Geometry: {self.subphoto_processing_frame.winfo_geometry()}")
        #     print(f"Top Right Frame Geometry: {self.top_right_frame.winfo_geometry()}")
        #     print(f"Subphoto Preview Frame Geometry: {self.subphoto_preview_frame.winfo_geometry()}")
        #     print(f"Primary User Input Frame Geometry: {self.primary_user_input_frame.winfo_geometry()}\n")

        # Step 1: Clear existing frames
        for widget in self.subphoto_preview_frame.winfo_children():
            widget.destroy()

        # Step 2: Compute the grid layout based on the number of subphotos
        # rows, columns = self.compute_grid_layout(self.combined_photo.num_subphotos)
        if self.combined_photo.num_subphotos == 3:
            rows, columns = 2, 2
        elif self.combined_photo.num_subphotos == 1:
            rows, columns = 1, 1
        else:
            rows, columns = 2, 2
        
        self.subphoto_processing_frame.update_idletasks()
        self.subphoto_preview_frame.update_idletasks()

        # # Get padding from widget configuration
        padx = int(self.subphoto_preview_frame.grid_info().get('padx', 0))
        pady = int(self.subphoto_preview_frame.grid_info().get('pady', 0))

        # if self.debug_mode:
        #     print(f"subphoto_preview_frame padx: {ipadx}  pady: {ipady}")

        # x, y, total_frame_width, total_frame_height = self.subphoto_processing_frame.grid_bbox(0, 1)
        x, y, total_frame_width, total_frame_height = self.subphoto_preview_frame.grid_bbox(0, 0)

        # Adjust dimensions accordingly
        max_slot_width = (total_frame_width - (2 * padx) - 1) // columns
        max_slot_height = (total_frame_height - (2 * pady) - 1) // rows

        for row in range(rows):
            self.subphoto_preview_frame.rowconfigure(row, weight=1, uniform="a")
        for col in range(columns):
            self.subphoto_preview_frame.columnconfigure(col, weight=1, uniform="a")

        # if self.debug_mode:
        #     print(f"Total Frame Width: {total_frame_width}  Total Frame Height: {total_frame_height}")
        #     print(f"Max Slot Width: {max_slot_width}  Max Slot Height: {max_slot_height}")

        # Keep track of subphoto frames for later processing
        subphoto_frames = []

        # Step 2: Construct the grid using LabelFrames
        subphoto_index = 0  # Track number of subphotos added
        for row in range(rows):
            for col in range(columns):
                if subphoto_index >= self.combined_photo.num_subphotos:
                    break

                # Create LabelFrame for subphoto
                frame = ttk.LabelFrame(
                    self.subphoto_preview_frame,
                    text=f"Subphoto {subphoto_index + 1}",
                    style="M_Subphoto_Preview.TLabelframe",
                    labelanchor="n"
                )
                frame.grid(
                    row=row,
                    column=col,
                    # padx=cell_padding,
                    # pady=cell_padding,
                    sticky=(N, S, E, W)
                )

                # Prevent frame resizing based on content
                # frame.grid_propagate(False)

                # Add frame to list for later population
                subphoto_frames.append((frame, subphoto_index))
                subphoto_index += 1

        self.subphoto_preview_frame.update_idletasks()

        index = 0
        # Step 3: Populate frames with scaled images
        for frame, index in subphoto_frames:
            # Get subphoto from the combined photo
            subphoto = self.combined_photo.subphotos[index]

            # Update the GUI to make sure frame size is correct
            # self.subphoto_preview_frame.update_idletasks()
            frame.rowconfigure(0, weight=1)
            frame.columnconfigure(0, weight=1)
            frame.update_idletasks()

        #     # Get available size for this frame using grid_bbox
        #     # x, y, width, height = frame.grid_bbox(0, 0)

        #     # print(f"Width: {width}  Height: {height}")

            # Get padding from widget configuration
            padx = int(frame.grid_info().get('padx', 0))
            pady = int(frame.grid_info().get('pady', 0))

            # if self.debug_mode:
            #     print(f"frame {index} padx: {padx}  pady: {pady}")

            # x, y, slot_width, slot_height = frame.grid_bbox(0, 0)
            slot_width = frame.winfo_width()
            slot_height = frame.winfo_height()

            # if self.debug_mode:
            #     print(f"frame {index} Slot Width: {slot_width}  Slot Height: {slot_height}")

            # Adjust for padding
            max_width = slot_width - 2 * padx - 1 # Adjust padding (if needed)
            max_height = slot_height - 2 * pady - 1 # Adjust padding (if needed)
            # if self.debug_mode:
            #     print(f"frame {index} Max Width: {max_width}  Max Height: {max_height}")
            # Scale the subphoto to fit within the frame
            scaled_subphoto = self.scale_subphoto(subphoto, max_width, max_height)

            # Convert to Tkinter-compatible format (from BGR to RGB)
            tk_subphoto = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(scaled_subphoto, cv2.COLOR_BGR2RGB)))

            # Place image inside the frame as a Label
            subphoto_label = ttk.Label(
                frame,
                image=tk_subphoto,
                anchor="center",
                style="Subphoto.TLabel"
            )
            subphoto_label.image = tk_subphoto  # Prevent garbage collection
            subphoto_label.grid(
                row=0,
                column=0,
                padx=padx,
                pady=pady,
                sticky=(N, S, E, W)
            )

            frame.update_idletasks()

        # Step 4: Update the base name label
        self.base_name_label.config(text=f"Previewing: {self.base_name}")

        # Step 5: Force the UI to refresh and update
        self.subphoto_preview_frame.update_idletasks()

        # if self.debug_mode:
        #     print("\nCheckpoint C: preview_all_subphotos")
        #     print(f"Preview Frame Geometry: {self.preview_frame.winfo_geometry()}")
        #     print(f"Combined Photo Frame Geometry: {self.combined_photo_frame.winfo_geometry()}")
        #     print(f"Subphoto Processing Frame Geometry: {self.subphoto_processing_frame.winfo_geometry()}")
        #     print(f"Top Right Frame Geometry: {self.top_right_frame.winfo_geometry()}")
        #     print(f"Subphoto Preview Frame Geometry: {self.subphoto_preview_frame.winfo_geometry()}")
        #     print(f"Primary User Input Frame Geometry: {self.primary_user_input_frame.winfo_geometry()}\n")
        #     print(f"\nSubphoto Preview Frame Grid Info: {self.subphoto_preview_frame.grid_info()}\n")

    def load_subphoto(self):
        """
        Displays a subphoto based on the given index, using the latest adjusted version if available.

        Args:
            index (int): Index of the subphoto within combined_photo.subphotos.
            part_number (int): Display number for user reference (1-based).
        """

        # if self.debug_mode:
        #     print(f"load_subphoto GUI Current Index: {self.combined_photo.current_index}")

        #     print("\nCheckpoint A: load_subphoto")
        #     print(f"Preview Frame Geometry: {self.preview_frame.winfo_geometry()}")
        #     print(f"Combined Photo Frame Geometry: {self.combined_photo_frame.winfo_geometry()}")
        #     print(f"Subphoto Processing Frame Geometry: {self.subphoto_processing_frame.winfo_geometry()}")
        #     print(f"Top Right Frame Geometry: {self.top_right_frame.winfo_geometry()}")
        #     print(f"Subphoto Preview Frame Geometry: {self.subphoto_preview_frame.winfo_geometry()}")
        #     print(f"Primary User Input Frame Geometry: {self.primary_user_input_frame.winfo_geometry()}\n")

        if self.combined_photo.current_index + 1 > self.combined_photo.num_subphotos:
            print(f"Error: Index {self.combined_photo.current_index} is out of range for subphotos.")
            return

        # Check if an adjusted version of this subphoto exists; otherwise, load from combined_photo
        if self.adjusted_photo is None:
            subphoto = self.combined_photo.subphotos[self.combined_photo.current_index]  # Retrieve original subphoto
            self.adjusted_photo = subphoto.copy()  # Store a modifiable version
            self.part_number = self.combined_photo.current_index + 1
            self.base_name_label.config(text=f"{self.combined_photo.base_name} - Part {self.part_number}")
        else:
            subphoto = self.adjusted_photo

        # Clear previous widgets in subphoto preview frame
        for widget in self.subphoto_preview_frame.winfo_children():
            widget.destroy()

        # Reset the frame layout to avoid previous constraints interfering
        for i in range(5):
            self.subphoto_preview_frame.rowconfigure(i, weight=0)
        for j in range(5):
            self.subphoto_preview_frame.columnconfigure(j, weight=0)

        self.subphoto_preview_frame.rowconfigure(0, weight=1, uniform="")
        self.subphoto_preview_frame.columnconfigure(0, weight=1, uniform="")

        # Get frame dimensions dynamically
        # self.subphoto_processing_frame.update_idletasks()
        self.subphoto_preview_frame.update_idletasks()

        # if self.debug_mode:
        #     print(f"Subphoto Preview Frame Children: {self.subphoto_preview_frame.winfo_children()}")
        #     print(f"Subphoto Preview Frame Grid Info: {self.subphoto_preview_frame.grid_info()}")
        #     print(f"Subphoto Preview Frame Geometry: {self.subphoto_preview_frame.winfo_geometry()}")

        # if self.debug_mode:
        #     print("\nCheckpoint B: load_subphoto")
        #     # print(f"Preview Frame Geometry: {self.preview_frame.winfo_geometry()}")
        #     # print(f"Combined Photo Frame Geometry: {self.combined_photo_frame.winfo_geometry()}")
        #     # print(f"Subphoto Processing Frame Geometry: {self.subphoto_processing_frame.winfo_geometry()}")
        #     # print(f"Top Right Frame Geometry: {self.top_right_frame.winfo_geometry()}")
        #     # print(f"Subphoto Preview Frame Geometry: {self.subphoto_preview_frame.winfo_geometry()}")
        #     # print(f"Primary User Input Frame Geometry: {self.primary_user_input_frame.winfo_geometry()}\n")

        # Get padding from widget configuration
        padx = int(self.subphoto_preview_frame.grid_info().get('padx', 0))
        pady = int(self.subphoto_preview_frame.grid_info().get('pady', 0))

        # x, y, slot_width, slot_height = self.subphoto_preview_frame.grid_bbox(0, 0)
        slot_width = self.subphoto_preview_frame.winfo_width()
        slot_height = self.subphoto_preview_frame.winfo_height()

        # Adjust dimensions accordingly
        max_width = slot_width - (2 * padx) - 1
        max_height = slot_height - (2 * pady) - 1
        
        # frame_width = int(self.subphoto_preview_frame.winfo_width() * self.single_subphoto_wscale)
        # frame_height = int(self.subphoto_preview_frame.winfo_height() * self.single_subphoto_hscale)
        # Apply padding around single preview image
        # single_preview_padding = 10  # Padding around the single image
        # max_width = frame_width - (2 * single_preview_padding)
        # max_height = frame_height - (2 * single_preview_padding)

        # Scale subphoto to fit the entire frame with padding
        scaled_subphoto = self.scale_subphoto(subphoto, max_width, max_height)

        # Convert BGR to RGB for Tkinter
        # tk_scaled_subphoto = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(scaled_subphoto, cv2.COLOR_BGR2RGB)))
        self.tk_scaled_subphoto = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(scaled_subphoto, cv2.COLOR_BGR2RGB)))

        # Display the preview image with padding
        self.preview_label = ttk.Label(
            self.subphoto_preview_frame,
            anchor='center',
            image=self.tk_scaled_subphoto,
            style='Subphoto.TLabel'
        )
        # preview_label.image = tk_scaled_subphoto  # Prevent garbage collection
        self.preview_label.grid(
            row=0,
            column=0,
            # padx=single_preview_padding,
            # pady=single_preview_padding,
            sticky=(N, S, E, W)
        )
        
        self.subphoto_preview_frame.update_idletasks()

        # if self.debug_mode:
        #     print(f"Subphoto Preview Frame Children: {self.subphoto_preview_frame.winfo_children()}")
        #     print(f"Subphoto Preview Frame Grid Info: {self.subphoto_preview_frame.grid_info()}")
        #     print(f"Subphoto Preview Frame Geometry: {self.subphoto_preview_frame.winfo_geometry()}")
        #     print(f"Preview Label Widget Geometry: {self.preview_label.winfo_geometry()}")

        # if self.debug_mode:
        #     print("\nCheckpoint C: load_subphoto")
        #     # print(f"Preview Frame Geometry: {self.preview_frame.winfo_geometry()}")
        #     # print(f"Combined Photo Frame Geometry: {self.combined_photo_frame.winfo_geometry()}")
        #     # print(f"Subphoto Processing Frame Geometry: {self.subphoto_processing_frame.winfo_geometry()}")
        #     # print(f"Top Right Frame Geometry: {self.top_right_frame.winfo_geometry()}")
        #     # print(f"Subphoto Preview Frame Geometry: {self.subphoto_preview_frame.winfo_geometry()}")
        #     # print(f"Primary User Input Frame Geometry: {self.primary_user_input_frame.winfo_geometry()}\n")

    def load_subphoto_processing_inputs(self):
        """
        Loads input fields for subphoto processing directly into primary_user_input_frame.
        """

        # self.subphoto_processing_frame.rowconfigure(2, minsize=self.preview_frame.winfo_height()//4)

        # Clear existing inputs
        for widget in self.primary_user_input_frame.winfo_children():
            widget.destroy()

        self.primary_user_input_frame.rowconfigure(0, weight=1)
        self.primary_user_input_frame.columnconfigure(0, weight=3)
        self.primary_user_input_frame.columnconfigure(1, weight=1)

        # Metadata Input Frame (3/4 width)
        self.metadata_input_frame = ttk.Frame(self.primary_user_input_frame, style="TFrame")
        self.metadata_input_frame.grid(
            row=0,
            column=0,
            sticky=(N, S, E, W)
            )
        self.metadata_input_frame.rowconfigure(0, weight=1)
        self.metadata_input_frame.rowconfigure(1, weight=1)
        self.metadata_input_frame.rowconfigure(2, weight=1)
        self.metadata_input_frame.rowconfigure(3, weight=1)
        self.metadata_input_frame.columnconfigure(0, weight=1)
        self.metadata_input_frame.columnconfigure(1, weight=1)
    
        # Year Entry
        ttk.Label(
            self.metadata_input_frame,
            text="Year (YYYY):",
            style="TLabel"
            ).grid(row=0, column=0, sticky=E, padx=5, pady=5)

        self.year_entry = ttk.Entry(self.metadata_input_frame, style="TEntry")
        self.year_entry.insert(0, self.last_year)
        self.year_entry.grid(
            row=0,
            column=1,
            sticky=W,
            padx=5,
            pady=5
            )
        self.year_entry.focus_set()  # Set focus to Year field

        # MMDD Entry
        ttk.Label(
            self.metadata_input_frame,
            text="Date (MMDD):",
            style="TLabel"
            ).grid(row=1, column=0, sticky=E, padx=5, pady=5)

        self.mmdd_entry = ttk.Entry(self.metadata_input_frame, style="TEntry")
        self.mmdd_entry.insert(0, self.last_mmdd)
        self.mmdd_entry.grid(
            row=1,
            column=1,
            sticky=W,
            padx=5,
            pady=5
            )

        # Description Dropdown
        ttk.Label(
            self.metadata_input_frame,
            text="Description:",
            style="TLabel"
            ).grid(row=2, column=0, sticky=E, padx=5, pady=5)

        self.description_var = StringVar(value=self.last_description)
        self.description_dropdown = ttk.Combobox(self.metadata_input_frame, textvariable=self.description_var, style="TCombobox")
        self.description_dropdown.grid(
            row=2,
            column=1,
            sticky=W,
            padx=5,
            pady=5
            )
        
        self.update_description_dropdown()  # Update dropdown

        # ttk.Label(
        #     self.metadata_input_frame,
        #     text="Test",
        #     style="TLabel"
        #     ).grid(row=3, column=0, sticky=E, padx=5, pady=5)
        
        self.metadata_input_frame.update_idletasks()

        # Confirm & Save Button (Right Side, 1/4 Width)
        confirm_button = ttk.Button(
            self.primary_user_input_frame,
            text="Confirm & Save",
            command=self.confirm_and_save,
            style="Confirm.TButton"
        )
        confirm_button.grid(
            row=0,
            column=1,
            padx=5,
            pady=5,
            sticky=(N, S, E, W)
            )
        
        self.primary_user_input_frame.update_idletasks()

    def confirm_and_process_subphotos(self):
        """
        Confirms the combined photo and proceeds to subphoto processing.
        """
        self.photo_discarded = False
        self.subphoto_processing_complete = False  # Reset completion flag
        self.load_subphoto_processing_inputs()  # Load the subphoto processing inputs
        self.subphoto_processing_frame.update_idletasks()
        self.load_subphoto()  # Load the first subphoto

        print(f"confirm_and_process_subphotos GUI Current Index: {self.combined_photo.current_index}")

        self.confirmation_variable.set("process_subphotos")  # Unique value indicating subphoto processing

    def confirm_and_save(self):
        """
        Confirms metadata, moves subphoto and metadata to the save queue,
        and increments the current index.
        """
        if not self.validate_metadata():
            return  # Stop if metadata is invalid

        self.last_year = self.year_entry.get()
        self.last_mmdd = self.mmdd_entry.get()
        self.last_description = self.description_var.get()

        # ✅ Add new description to history if not already present
        if self.last_description and self.last_description not in self.description_history:
            self.description_history.add(self.last_description)
            self.update_description_dropdown()  # ✅ Update dropdown

        # ✅ Directly put `adjusted_photo` in the save queue instead of storing it in `output_photo`
        self.save_queue.put({
            # "photo": self.adjusted_photo.copy(),  # ✅ Enqueue directly
            "photo": self.adjusted_photo,
            "base_name": self.combined_photo.base_name,
            "part_number": self.part_number,
            "metadata": self.get_metadata()
        })

        # ✅ Free memory by clearing adjusted_photo
        self.adjusted_photo = None

        # Signal that the subphoto has been saved
        self.confirmation_variable.set("save_subphoto")

        # Move to the next subphoto
        if self.combined_photo.current_index + 1 < self.combined_photo.num_subphotos:
            self.combined_photo.current_index += 1
            self.load_subphoto()
            self.root.update_idletasks()
        else:
            self.subphoto_processing_complete = True
            self.indicate_waiting_for_photos()  # Reset GUI

    def discard_and_reprocess(self):
        """
        Discards the current photo and triggers a rerun of the split_and_enqueue_photos function.
        """
        # if Tk.messagebox.askyesno("Discard and Reprocess", "Are you sure you want to discard this photo and reprocess with different parameters?"):
            # Signal that the current photo is discarded
        self.photo_discarded = True  # Mark the photo as discarded
        self.confirmation_variable.set("reprocess")

    def validate_metadata(self):
        """
        Validates the metadata fields for Year and MMDD using datetime.

        Returns:
            bool: True if validation passes, False otherwise.
        """
        year = self.year_entry.get()
        mmdd = self.mmdd_entry.get()

        try:
            # Validate year as a 4-digit number within a reasonable range
            current_year = datetime.now().year
            if not (1800 <= int(year) <= current_year):
                raise ValueError(f"Year must be between 1800 and {current_year}.")

            # Combine year and MMDD to check if it's a valid date
            date_string = f"{year}{mmdd}"
            datetime.strptime(date_string, "%Y%m%d")
        except ValueError as e:
            # messagebox.showerror("Invalid Metadata", str(e))
            return False

        return True

    def rotate_right(self):
        if self.adjusted_photo is not None:
            self.adjusted_photo = cv2.rotate(self.adjusted_photo, cv2.ROTATE_90_CLOCKWISE)
            self.load_subphoto()
        else:
            print("No image loaded. Cannot rotate.")

    def rotate_left(self):
        if self.adjusted_photo is not None:
            self.adjusted_photo = cv2.rotate(self.adjusted_photo, cv2.ROTATE_90_COUNTERCLOCKWISE)
            self.load_subphoto()
        else:
            print("No image loaded. Cannot rotate.")

    def flip_horizontal(self):
        if self.adjusted_photo is not None:
            self.adjusted_photo = cv2.flip(self.adjusted_photo, 1)
            self.load_subphoto()
        else:
            print("No image loaded. Cannot flip.")

    def flip_vertical(self):
        if self.adjusted_photo is not None:
            self.adjusted_photo = cv2.flip(self.adjusted_photo, 0)
            self.load_subphoto()
        else:
            print("No image loaded. Cannot flip.")

    def reduce_noise(self):
        if self.adjusted_photo is not None:
            self.adjusted_photo = cv2.fastNlMeansDenoisingColored(
                self.adjusted_photo,
                None,
                10,
                10,
                7,
                21
                )
            self.load_subphoto()
        else:
            print("No image loaded. Cannot reduce noise.")

    def cuda_reduce_noise(self):
        if self.adjusted_photo is not None:
            gpu_image = cv2.cuda_GpuMat()
            gpu_image.upload(self.adjusted_photo)
            cv2.cuda.fastNlMeansDenoisingColored(
                src = gpu_image,
                h_luminance = 10,
                photo_render = 10,
                search_window = 21,
                block_size = 7,
                )
            self.adjusted_photo = gpu_image.download()
            self.load_subphoto()
        else:
            print("No image loaded. Cannot reduce noise.")

    def quit_app(self):
        """
        Gracefully shuts down the application by stopping background threads
        and closing the GUI.
        """
        print("Quitting application...")

        # Signal all threads to stop
        self.stop_event.set()  # Notify background threads

        # Trigger confirmation variable to unblock any waiting threads
        self.confirmation_variable.set("quit_app")

        # Wait for all background threads to stop before closing the GUI
        self.root.after(100, self._safe_exit)  # Schedule safe exit

    def _safe_exit(self):
        """
        Ensures all background threads are stopped before exiting the GUI.
        """
        # Check if background threads have stopped
        if threading.active_count() > 1:
            # Keep checking every 100ms until threads finish
            self.root.after(100, self._safe_exit)
        else:
            # All threads are done, safe to close the GUI
            self.root.quit()
            self.root.destroy()

    def get_metadata(self):
        return {
            "year": self.year_entry.get(),
            "mmdd": self.mmdd_entry.get(),
            "description": self.description_var.get()
        }

    def update_description_dropdown(self):
        """
        Updates the description dropdown with the latest unique descriptions.
        """
        # Sort descriptions alphabetically (optional)
        sorted_descriptions = sorted(self.description_history)

        # ✅ Update dropdown values
        self.description_dropdown['values'] = sorted_descriptions
    
    def indicate_waiting_for_photos(self):
        """
        Displays a large "Waiting for photos..." message in the subphoto preview frame.
        """

        # if self.debug_mode:
        #     print("\nDEBUG: Indicating waiting for photos...")
        #     print(f"subphoto_preview_frame width: {self.subphoto_preview_frame.winfo_width()}")
        #     print(f"subphoto_preview_frame height: {self.subphoto_preview_frame.winfo_height()}")
        #     print(f"subphoto_preview_frame grid info: {self.subphoto_preview_frame.grid_info()}")

        # Clear any existing content in the subphoto preview frame
        for widget in self.subphoto_preview_frame.winfo_children():
            widget.destroy()

        # Create and place a large label in the center of the subphoto preview frame
        waiting_label = ttk.Label(
            self.subphoto_preview_frame,
            text="Waiting for new input photo...",
            style="TLabel",
            anchor="center",
            font=("Arial", 36, "bold")
        )

        # Center the label in the preview frame
        waiting_label.grid(
            row = 0,
            column= 0,
            padx=5,
            pady=5,
            sticky=(N, S, E, W)
        )

        # self.waiting_label.grid(
        #     row=0,
        #     column=0,
        #     sticky=(N, S, E, W)
        # )

        # Force an update to ensure the UI refreshes immediately
        self.subphoto_preview_frame.update_idletasks()

    def run(self):
        """Run the GUI main loop."""
        self.root.mainloop()

    def choose_file_dialog(self):
        """
        Opens a file dialog to manually choose a file from the ingest folder.
        """
        ingest_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingest")
        
        file_path = filedialog.askopenfilename(
            initialdir=ingest_folder,
            title="Select File to Simulate",
            filetypes=(("Image Files", "*.jpg *.png *.tiff *.tif *.jpeg *.bmp *.heic *.webp"), ("All Files", "*.*"))
        )

        if file_path:
            filename = os.path.basename(file_path)
            self.simulate_ingest_file(filename)

    def simulate_ingest_file(self, filename=None):
        """
        Simulates a file appearing in the ingest folder by copying it to a temporary 
        location one level above, deleting the original, and restoring it with the same filename.
        """
        ingest_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ingest")
        parent_folder = os.path.dirname(ingest_folder)  # One level above the ingest folder

        try:
            files = [f for f in os.listdir(ingest_folder) if os.path.isfile(os.path.join(ingest_folder, f))]

            if not files:
                print("No files found in the ingest folder to simulate.")
                return

            # Select the file to simulate
            if filename:
                if filename not in files:
                    print(f"File '{filename}' not found in the ingest folder.")
                    return
                file_to_simulate = filename
            else:
                file_to_simulate = files[0]  # Default to the first file

            original_path = os.path.join(ingest_folder, file_to_simulate)
            temp_copy_path = os.path.join(parent_folder, file_to_simulate)  # Keep the original filename

            # Step 1: Copy the file to one level above the ingest folder
            shutil.copy2(original_path, temp_copy_path)
            print(f"Copied '{file_to_simulate}' to '{parent_folder}' temporarily.")

            # Step 2: Delete the original file in the ingest folder
            os.remove(original_path)
            print(f"Deleted the original file: {file_to_simulate}.")

            time.sleep(1)  # Allow time for the monitoring thread to detect deletion

            # Step 3: Move the file back to the ingest folder (triggers on_created event)
            shutil.move(temp_copy_path, original_path)
            print(f"Simulated file appearance for '{file_to_simulate}' (original name preserved).")

            # Update the GUI status bar if available
            self.status_label.config(text=f"Simulated file appearance: {file_to_simulate}")

        except Exception as e:
            print(f"Error simulating file appearance: {e}")

    def change_font(self):
        """
        Creates a top-level window for customizing fonts during runtime.
        Allows users to choose a font family and size.
        """
        # Create a new window for font customization
        font_window = Toplevel(self.root)
        font_window.title("Change Font")
        font_window.geometry("400x300")

        # Configure grid layout with padding
        font_window.columnconfigure(0, weight=1, pad=10)
        font_window.columnconfigure(1, weight=1, pad=10)

        # Font family selector
        font_label = ttk.Label(font_window, text="Font Family:")
        font_label.grid(row=0, column=0, sticky=W, padx=10, pady=10)

        font_families = list(font.families())  # Retrieve available font families
        selected_font_family = StringVar(value=self.default_font)  # Default font family
        font_family_dropdown = ttk.Combobox(
            font_window, textvariable=selected_font_family, values=font_families
        )
        font_family_dropdown.grid(row=0, column=1, sticky=E, padx=10, pady=10)

        # Font size selector
        size_label = ttk.Label(font_window, text="Font Size:")
        size_label.grid(row=1, column=0, sticky=W, padx=10, pady=10)

        font_size = IntVar(value=self.base_font_size)  # Default font size
        font_size_spinbox = Spinbox(
            font_window, from_=8, to=72, textvariable=font_size, width=5
        )
        font_size_spinbox.grid(row=1, column=1, sticky=E, padx=10, pady=10)

        font_color_label = ttk.Label(font_window, text="Font Color:")
        font_color_label.grid(row=2, column=0, sticky=W, padx=10, pady=10)

        selected_font_color = self.text_color
        font_color_selector = ttk.Combobox(
            font_window,
            textvariable=selected_font_color,
            values=('white', 'black')
        )
        font_color_selector.grid(row=2, column=1, sticky=E, padx=10, pady=10)

        # Apply changes button
        def apply_font_changes():
            """
            Applies the selected font changes and updates the application styles.
            """
            self.default_font = selected_font_family.get()
            self.base_font_size = font_size.get()
            self.text_color = font_color_selector.get()
            self.define_styles()  # Reapply styles with the new font settings
            self.root.update_idletasks()  # Refresh the GUI immediately
            font_window.destroy()  # Close the font customization window

        apply_button = ttk.Button(
            font_window, text="Apply", command=apply_font_changes
        )
        apply_button.grid(row=5, column=0, columnspan=2, pady=20)

    def change_photo_scaling(self):
        """
        Creates a top-level window for customizing fonts during runtime.
        Allows users to choose a font family and size.
        """
        # Create a new window for font customization
        scaling_window = Toplevel(
            self.main_frame,
            background=self.bg_color_1
            # title="Change Photo Display Scaling"
            )
        scaling_window.title("Change Photo Display Scaling")
        # scaling_window.geometry("400x300")
        scaling_window.attributes("-topmost", True)

        # Configure grid layout with padding
        scaling_window.columnconfigure(0, weight=2, pad=10)
        scaling_window.columnconfigure(1, weight=1, pad=10)
        scaling_window.columnconfigure(2, weight=1, pad=10)
        scaling_window.columnconfigure(3, weight=2, pad=10)
        scaling_window.columnconfigure(4, weight=1, pad=10)

        # Single Subphoto Width Scaling
        ssub_wscale_label = ttk.Label(scaling_window, text="Single Subphoto Width Scale:")
        ssub_wscale_label.grid(row=0, column=3, sticky=W, padx=10, pady=10)

        ssub_wscale = DoubleVar(value=self.single_subphoto_wscale)
        ssub_wscale_spinbox = Spinbox(
            scaling_window,
            from_=0.50,
            to=1.00,
            increment=0.05,
            textvariable=ssub_wscale,
            width=10
        )
        ssub_wscale_spinbox.grid(row=0, column=4, sticky=E, padx=10, pady=10)

        # Single Subphoto Height Scaling
        ssub_hscale_label = ttk.Label(scaling_window, text="Single Subphoto Height Scale:")
        ssub_hscale_label.grid(row=1, column=3, sticky=W, padx=10, pady=10)

        ssub_hscale = DoubleVar(value=self.single_subphoto_hscale)
        ssub_hscale_spinbox = Spinbox(
            scaling_window,
            from_=0.50,
            to=1.00,
            increment=0.05,
            textvariable=ssub_hscale,
            width=10
        )
        ssub_hscale_spinbox.grid(row=1, column=4, sticky=E, padx=10, pady=10)

        # Multi Subphoto Width Scaling
        msub_wscale_label = ttk.Label(scaling_window, text="Multi Subphoto Width Scale:")
        msub_wscale_label.grid(row=0, column=0, sticky=W, padx=10, pady=10)

        msub_wscale = DoubleVar(value=self.multi_subphoto_wscale)
        msub_wscale_spinbox = Spinbox(
            scaling_window,
            from_=0.50,
            to=1.00,
            increment=0.05,
            textvariable=msub_wscale,
            width=10
        )
        msub_wscale_spinbox.grid(row=0, column=1, sticky=E, padx=10, pady=10)

        # Multi Subphoto Height Scaling
        msub_hscale_label = ttk.Label(scaling_window, text="Multi Subphoto Height Scale:")
        msub_hscale_label.grid(row=1, column=0, sticky=W, padx=10, pady=10)

        msub_hscale = DoubleVar(value=self.multi_subphoto_hscale)
        msub_hscale_spinbox = Spinbox(
            scaling_window,
            from_=0.50,
            to=1.00,
            increment=0.05,
            textvariable=msub_hscale,
            width=10
        )
        msub_hscale_spinbox.grid(row=1, column=1, sticky=E, padx=10, pady=10)

        # Apply changes button
        def apply_multi_scaling_changes():
            self.multi_subphoto_wscale = msub_wscale.get()
            self.multi_subphoto_hscale = msub_hscale.get()

            self.preview_all_subphotos(self.combined_photo)

            # scaling_window.destroy()  # Close the font customization window

        def apply_single_scaling_changes():
            self.single_subphoto_wscale = ssub_wscale.get()
            self.single_subphoto_hscale = ssub_hscale.get()

            self.load_combined_image()
            self.load_subphoto()

            # scaling_window.destroy()  # Close the font customization window

        apply_multi_button = ttk.Button(
            scaling_window, text="Apply to Multi", command=apply_multi_scaling_changes
        )
        apply_multi_button.grid(row=4, column=0, columnspan=2, pady=10)

        apply_single_button = ttk.Button(
            scaling_window, text="Apply to Single", command=apply_single_scaling_changes
        )
        apply_single_button.grid(row=4, column=3, columnspan=2, pady=10)

        divider = ttk.Separator(scaling_window, orient=VERTICAL)
        divider.grid(
            row=0,
            column=2,
            rowspan=5,
            sticky=(N, S)
        )

    def get_display_scaling(self):
        # # Windows DPI Awareness
        # if self.root.tk.call("tk", "windowingsystem") == "win32":
        #     self.scaling_factor = self.root.tk.call("tk", "scaling")  # Get Tkinter scaling factor
        # else:
        #     # self.scaling_factor = self.root.winfo_fpixels('1i') / 96  # macOS/Linux method
        #     self.scaling_factor = 1

        self.root.tk.call("tk", "scaling", 1.0)  # Forces 100% scaling if Windows is misreporting
        self.root.update_idletasks()
        self.scaling_factor = self.root.tk.call("tk", "scaling")  # Get Tkinter scaling factor

    def display_debug_plot(self, plot_type=None):
        """
        Dynamically generates and displays debug plots based on available plot data.
        Supports multiple plot types including detected lines, skew angles, edge detection, 
        and horizontal boundary projections.

        Parameters:
            plot_type (str): Optional. The specific plot type to display.
                            If None, defaults to the first available plot.
        """
        # 🔍 1. Automatically detect available plots from the debug data
        available_plots = list(self.combined_photo.debug_data.plot_data.keys())
        
        # Set the default plot type if none is specified
        if not plot_type:
            # plot_type = available_plots[0]  # Select the first available plot type
            # plot_type = "horizontal_boundaries_plot"  # Default to horizontal boundaries
            plot_type = "horizontal_boundaries_plot"  # Default to detected lines

        # 🔍 2. Retrieve the corresponding plot data from debug data
        plot_data = self.combined_photo.debug_data.plot_data.get(plot_type, None)
        if not plot_data:
            print(f"No data available for plot type: {plot_type}")
            return  # Exit early if no data for the specified plot type exists

        # 🪟 3. Create a new top-level Tkinter window for the debug plot
        debug_window = Toplevel(self.main_frame)
        debug_window.title(f"Debug Plot - {plot_type.replace('_', ' ').title()}")

        # 🔠 4. Configure Matplotlib font settings for consistent plot appearance
        plt.rcParams.update({
            'font.size': 16,           # Base font size for text
            'axes.titlesize': 24,      # Font size for subplot titles
            'axes.labelsize': 16,      # Font size for x and y labels
            'legend.fontsize': 14,     # Font size for legend
            'figure.titlesize': 28     # Font size for the figure title
        })

        # 🖥️ 5. Create a Matplotlib figure and axis for the plot
        # fig, ax = plt.subplots(figsize=(24, 14), dpi=100)
        fig = Figure(figsize=(24, 14), dpi=100)

        # 🔄 6. Select the appropriate plotting function based on the plot type
        if "detected_lines" in plot_type:
            self._plot_detected_lines_on_subphoto(fig, plot_data)
        elif "horizontal_boundaries_plot" in plot_type:
            self._plot_horizontal_boundaries(fig, plot_data)
        # elif "edges_subregion" in plot_type:
        #     self._plot_edges_subregion(fig, plot_data)
        # elif "skew_angle_plot" in plot_type:
        #     self._plot_skew_angle(ax, plot_data)
        # elif "edge_detection_plot" in plot_type:
        #     self._plot_edge_detection(ax, plot_data)
        else:
            # Display a message for unsupported plot types
            ax = fig.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, "Unsupported Plot Type", ha='center', va='center', fontsize=32)

        # 🖼️ 7. Embed the Matplotlib plot in the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=debug_window)
        canvas.draw()  # Draw the initial plot

        # 🛠️ 8. Add an interactive toolbar (zoom, pan, save) to the plot
        toolbar = NavigationToolbar2Tk(canvas, debug_window, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(side=TOP, fill=X)  # Place the toolbar at the top of the window
        canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)  # Make the plot resizable

        # 🔄 9. Dropdown menu to switch between available plot types dynamically
        def switch_plot(new_plot_type):
            debug_window.destroy()  # Close the current plot window
            self.display_debug_plot(new_plot_type)  # Open a new plot window for the selected type

        dropdown_frame = Frame(debug_window)
        dropdown_frame.pack(side=BOTTOM, fill=X)

        # Dropdown widget for selecting plot types
        plot_selector = StringVar(value=plot_type)
        plot_dropdown = OptionMenu(
            dropdown_frame, plot_selector, *available_plots, command=switch_plot
        )
        plot_dropdown.pack(side=LEFT, padx=10, pady=5)

        # ❌ 10. Handle closing the window properly (to avoid memory leaks)
        def on_close():
            plt.close(fig)  # Close the Matplotlib figure
            debug_window.destroy()  # Destroy the Tkinter window

        # Attach the close event handler
        debug_window.protocol("WM_DELETE_WINDOW", on_close)

    def old_display_debug_plot(self, plot_key="horizontal_boundaries_plot"):
        """
        Dynamically generate and display a debug plot using raw data.
        """
        debug_window = Toplevel(self.main_frame)
        debug_window.title("Debug Plot")
        # debug_window.attributes("-topmost", True)

        plot_data = self.combined_photo.debug_data.plot_data.get(plot_key, None)

        # Set global font sizes
        plt.rcParams.update({
            'font.size': 18,          # Base font size
            'axes.titlesize': 24,     # Font size for subplot titles
            'axes.labelsize': 20,     # Font size for x and y labels
            # 'xtick.labelsize': 10,    # Font size for x-axis tick labels
            # 'ytick.labelsize': 10,    # Font size for y-axis tick labels
            'legend.fontsize': 18,    # Font size for the legend
            'figure.titlesize': 32    # Font size for the main figure title
        })

        if plot_data:
            fig, ax = plt.subplots(figsize=(24, 12), dpi=100)

            if plot_key == "horizontal_boundaries_plot":
                # Generate the plot from raw data
                smoothed_projection = plot_data["smoothed_projection"]
                exaggerated_projection = plot_data["exaggerated_projection"]
                boundary_threshold = plot_data["boundary_threshold"]
                boundaries = plot_data["boundaries"]
                
                ax.plot(
                    smoothed_projection,
                    label="Smoothed Projection",
                    color="blue"
                )
                ax.plot(
                    exaggerated_projection,
                    label="Exaggerated Projection",
                    color="orange",
                    linestyle="--"
                )
                ax.axhline(
                    y=boundary_threshold,
                    color="red",
                    linestyle="--",
                    label="Boundary Threshold"
                )

                for boundary in boundaries:
                    ax.axvline(x=boundary, color="green", linestyle="--", label=f"Boundary {boundary}")

                ax.set_title("Horizontal Boundary Detection")
                ax.set_xlabel("Row Index")
                ax.set_ylabel("Projection Value")
                ax.legend()

            # if plot_key == "skew_angle_plot_0":

            # Display the plot using Tkinter
            canvas = FigureCanvasTkAgg(fig, master=debug_window)
            # canvas_widget = canvas.get_tk_widget()
            canvas.draw()

            toolbar = NavigationToolbar2Tk(canvas, debug_window, pack_toolbar=False)
            toolbar.update()

            toolbar.pack(side=TOP, fill=X)
            canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=True)

        # # Resize plot when the window size changes
        # def on_resize(event):
        #     width, height = event.width, event.height
        #     fig.set_size_inches(width / 100, height / 100)  # Resize figure to match window size
        #     canvas.draw()

        # debug_window.bind("<Configure>", on_resize)

        def on_close():
            # plt.close(fig)
            debug_window.destroy()

        debug_window.protocol("WM_DELETE_WINDOW", on_close)

    def _plot_horizontal_boundaries(self, fig, plot_data):
        ax = fig.add_subplot(1, 1, 1)
        smoothed_projection = plot_data["smoothed_projection"]
        exaggerated_projection = plot_data["exaggerated_projection"]
        boundary_threshold = plot_data["boundary_threshold"]
        boundaries = plot_data["boundaries"]

        ax.plot(smoothed_projection, label="Smoothed Projection", color="blue")
        ax.plot(exaggerated_projection, label="Exaggerated Projection", color="orange", linestyle="--")
        ax.axhline(y=boundary_threshold, color="red", linestyle="--", label="Boundary Threshold")

        for boundary in boundaries:
            ax.axvline(x=boundary, color="green", linestyle="--", label=f"Boundary {boundary}")

        ax.set_title("Horizontal Boundary Detection")
        ax.set_xlabel("Row Index")
        ax.set_ylabel("Projection Value")
        ax.legend()

    def _plot_detected_lines_on_subphoto(self, fig, plot_data):
        """
        Draws detected lines on the raw subphoto using its own subplot.
        """
        ax = fig.add_subplot(1, 1, 1)  # Create a single subplot
        index = plot_data["index"]
        lines = plot_data["lines"]
        margin = plot_data["margin"]
        # subphoto = self.combined_photo.debug_data.raw_subphotos[index]
        edges = self.combined_photo.debug_data.edges_subregions[index]

        edges_width = edges.shape[1]
        edges_height = edges.shape[0]

        # max_subphoto_w = fig.get_figwidth() * fig.dpi
        # max_subphoto_h = fig.get_figheight() * fig.dpi
        # print(f"max_subphoto_w: {max_subphoto_w}, max_subphoto_h: {max_subphoto_h}")
        # scaled_subphoto = self.scale_subphoto(subphoto, max_subphoto_w, max_subphoto_h)
        # print(f"scaled_subphoto shape: {scaled_subphoto.shape}")
        # Convert BGR to RGB
        # subphoto_rgb = cv2.cvtColor(scaled_subphoto, cv2.COLOR_BGR2RGB)
        # subphoto_rgb = cv2.cvtColor(subphoto, cv2.COLOR_BGR2RGB)
        # ax.imshow(subphoto_rgb)
        ax.imshow(edges, cmap='gray', vmin=0, vmax=255)

        # Draw detected lines
        for line in lines:
            rho = line["rho"]
            theta = line["theta"]
            region = line["region"]

            # Convert rho, theta to line coordinates
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a * rho
            y0 = b * rho

            line_length = 1000  # Arbitrary large number for extending the line
            x1 = x0 + line_length * (-b)
            y1 = y0 + line_length * a
            x2 = x0 - line_length * (-b)
            y2 = y0 - line_length * a

            # Step 2️⃣: Clip the coordinates to the subregion bounds
            xmin, ymin, xmax, ymax = 0, 0, edges_width, edges_height

            # Clip x-coordinates
            x1_clipped = max(xmin, min(x1, xmax))
            x2_clipped = max(xmin, min(x2, xmax))

            # Clip y-coordinates
            y1_clipped = max(ymin, min(y1, ymax))
            y2_clipped = max(ymin, min(y2, ymax))

            color = "cyan" if region == "left" else "magenta"
            ax.plot([x1_clipped, x2_clipped], [y1_clipped, y2_clipped], color=color, linewidth=2)

        # Add margins
        ax.axvline(x=margin, color="yellow", linestyle="--", linewidth=1, label="Left Margin")
        ax.axvline(x=edges_width - margin, color="yellow", linestyle="--", linewidth=1, label="Right Margin")

        ax.set_title("Detected Lines Overlaid on Subphoto")
        ax.axis("off")
        ax.legend()

    # def prompt_for_new_config(self, current_config):
    #     """
    #     Prompts the user to input new configuration parameters for reprocessing with a scrollable popup.

    #     Args:
    #         current_config (dict): The current configuration dictionary.

    #     Returns:
    #         dict: The updated configuration dictionary.
    #     """
    #     new_config = current_config.copy()

    #     # Create a popup dialog
    #     config_window = tk.Toplevel(self.root)
    #     config_window.title("Update Configuration Parameters")
    #     config_window.geometry("400x400")
    #     config_window.grab_set()  # Make this dialog modal

    #     # Create a canvas and a frame to hold the configuration fields
    #     canvas = ttk.Canvas(config_window)
    #     scrollbar = ttk.Scrollbar(config_window, orient=tk.VERTICAL, command=canvas.yview)
    #     scrollable_frame = ttk.Frame(canvas)

    #     # Configure the canvas and scrollbar
    #     scrollable_frame.bind(
    #         "<Configure>",
    #         lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    #     )
    #     canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    #     canvas.configure(yscrollcommand=scrollbar.set)

    #     # Layout canvas and scrollbar
    #     canvas.pack(side=Tk.LEFT, fill=tk.BOTH, expand=True)
    #     scrollbar.pack(side=Tk.RIGHT, fill=tk.Y)

    #     # Add a label at the top
    #     tk.Label(scrollable_frame, text="Update Parameters", font=("Helvetica", 14)).pack(pady=10)

    #     # Create entry fields for the configuration parameters
    #     entries = {}
    #     for idx, (key, value) in enumerate(current_config.items()):
    #         tk.Label(scrollable_frame, text=f"{key}:", anchor="w").pack(fill="x", padx=10, pady=5)

    #         entry = tk.Entry(scrollable_frame)
    #         entry.insert(0, str(value))  # Pre-fill with the current value
    #         entry.pack(fill="x", padx=10, pady=5)
    #         entries[key] = entry

    #     def save_and_close():
    #         # Update the configuration with the user's inputs
    #         for key, entry in entries.items():
    #             try:
    #                 user_input = entry.get()
    #                 # Handle booleans explicitly
    #                 if isinstance(current_config[key], bool):
    #                     if user_input.lower() in ["true", "1", "yes"]:
    #                         new_config[key] = True
    #                     elif user_input.lower() in ["false", "0", "no"]:
    #                         new_config[key] = False
    #                     else:
    #                         raise ValueError(f"Invalid boolean value for {key}: {user_input}")
    #                 # Handle integers
    #                 elif isinstance(current_config[key], int):
    #                     new_config[key] = int(user_input)
    #                 # Handle floats
    #                 elif isinstance(current_config[key], float):
    #                     new_config[key] = float(user_input)
    #                 # Handle tuples (e.g., Canny_Threshold_Scale)
    #                 elif isinstance(current_config[key], tuple):
    #                     try:
    #                         # Parse user input as a tuple of floats
    #                         new_config[key] = tuple(map(float, user_input.strip("()").split(",")))
    #                     except ValueError:
    #                         raise ValueError(f"Invalid tuple format for {key}: {user_input}")
    #                 # Handle strings
    #                 else:
    #                     new_config[key] = user_input
    #             except ValueError as e:
    #                 messagebox.showerror("Invalid Input", str(e))
    #                 return
    #         config_window.destroy()

    #     # Add Save and Cancel buttons at the bottom
    #     tk.Button(scrollable_frame, text="Save", command=save_and_close).pack(pady=10)
    #     tk.Button(scrollable_frame, text="Cancel", command=config_window.destroy).pack(pady=5)

    #     config_window.wait_window()  # Wait for the dialog to close
    #     return new_config
