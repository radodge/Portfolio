# config.py

import os
import cv2

# Define a shared application root path
APPLICATION_ROOT = os.path.dirname(os.path.abspath(__file__))

# ✅ Default test bench settings
test_config = {
    "start_folder": os.path.join(APPLICATION_ROOT, "iPhone"),
    "start_index": 2,
    "save_directory": os.path.join(APPLICATION_ROOT, "output_images")
}

gui_config = {
    "window_title": "Corner Detection Test Bench",
    "monitor_number": 1,
    "major_adjustment": 25,
    "minor_adjustment": 5,
    "magnifier_size": 150,  # n x n crop size in full-resolution pixels

}

class CornerDetectionConfig:
    """
    Stores and manages tunable parameters for corner detection.
    """

    def __init__(self):
        self.CUDA_ENABLED = True
        self.SINGLE_PHOTO = True
        self.ANGLE_TOLERANCE = 10

        # Gaussian blur settings
        self.blur_config = {
            "kernel_w": 9,
            # "kernel_h": 7,
            "sigma_X": 500.0,
            "sigma_Y": 0.0
        }

        self.canny_config = {
            "lowThreshold": 420,
            "highThreshold": 500,
            "kernel_size": 5,
            "L2gradient": True
        }

        self.morph_config = {
            # "op": cv2.MORPH_CLOSE,
            # "srcType": cv2.CV_8UC1,
            "morph_kernel_w": 3,
            "iterations": 1
        }

        self.hough_config = {
            "rho": 5.0,
            "theta": 0.001,
            "minLineLength": 1500,
            "maxLineGap": 250,
            "maxLines": 100,
            "threshold": 1750
        }

    def to_dict(self):
        """
        Flattens both config groups into a single dictionary for UI editing.
        Does NOT include CUDA_Enabled (which is treated separately).
        """
        return {
            **self.blur_config,
            **self.canny_config,
            **self.morph_config,
            **self.hough_config,
            # self.morph_config["morph_kernel_w"]: self.morph_config["morph_kernel_w"],
        }

    def to_blur_tuple(self):
        """
        Returns a (ksize, sigma_x, sigma_y) tuple for use in Gaussian filters.
        """
        bc = self.blur_config
        return (bc["kernel_w"], bc["kernel_w"]), bc["sigma_X"], bc["sigma_Y"]
