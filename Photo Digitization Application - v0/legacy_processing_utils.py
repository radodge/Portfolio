import subprocess
import os
import shutil
import cv2
from cv2 import cuda
import numpy as np
from PIL import Image
import pillow_heif
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
# from matplotlib.gridspec import GridSpec

class ErrorInfo:
    def __init__(self, error_type, message):
        """
        Represents an error encountered during processing.

        Args:
            error_type (str): A short identifier for the error type.
            message (str): A human-readable description of the error.
        """
        self.error_type = error_type
        self.message = message

    def __str__(self):
        return f"[{self.error_type}] {self.message}"
    
class DebugData:
    def __init__(self):
        self.raw_subphotos = []
        self.edges_subregions = []
        self.detected_boundaries = []
        self.intermediate_outputs = {}
        self.plot_data = {}  # Store raw data for plots

    def add_raw_subphoto(self, subphoto):
        self.raw_subphotos.append(subphoto)

    def add_edges_subregion(self, edges_region):
        self.edges_subregions.append(edges_region)

    def add_detected_boundaries(self, boundaries):
        self.detected_boundaries = boundaries

    def add_intermediate_output(self, key, data):
        self.intermediate_outputs[key] = data

    def add_plot_data(self, key, data):
        """Store raw plot data like projections or thresholds."""
        self.plot_data[key] = data

    def clear(self):
        self.raw_subphotos.clear()
        self.edges_subregions.clear()
        self.detected_boundaries.clear()
        self.intermediate_outputs.clear()
        self.plot_data.clear()

def load_image_as_numpy_array(file_path):
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
        # HEIC Handling (Uses Pillow-HEIF, but converts from RGB to BGR)
        if file_path.lower().endswith(".heic"):
            heif_image = pillow_heif.open_heif(file_path)
            img = Image.frombytes(heif_image.mode, heif_image.size, heif_image.data)
            img_array = np.array(img)  # This is in RGB format

            # Convert from RGB to BGR to match OpenCV's default format
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        else:
            # Load image using OpenCV (BGR format by default)
            img_array = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

        if img_array is None:
            raise RuntimeError(f"Failed to load {file_path} using OpenCV.")

        return img_array  # Return image in BGR format

    except Exception as e:
        print(f"Failed to load image file {file_path}: {e}")
        return None

def convert_to_grayscale(image, processing_config):
    """
    Converts an image to grayscale using OpenCV.

    Args:
        image (np.ndarray): Input image in BGR format.

    Returns:
        np.ndarray: Grayscale image.
        GpuMat: Grayscale image on GPU if CUDA is enabled.
    """
    cuda_enabled = processing_config.get("CUDA_Enabled", False)

    if cuda_enabled:
        # Convert to grayscale using CUDA
        gpu_image = cuda.GpuMat()
        gpu_image.upload(image)
        gpu_grayscale = cuda.cvtColor(gpu_image, cv2.COLOR_BGR2GRAY)
        return gpu_grayscale
    
    else:
        # Convert to grayscale using CPU
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

def compute_canny_thresholds(grayscale_image, processing_config):
    cuda_enabled = processing_config.get("CUDA_Enabled", False)
    if cuda_enabled and isinstance(grayscale_image, cuda.GpuMat):
        # Download the grayscale image from GPU
        grayscale_image = grayscale_image.download()
    
    otsu_threshold, _ = cv2.threshold(grayscale_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    T1 = 0.5 * otsu_threshold  # Lower threshold
    # T2 = otsu_threshold  # Upper threshold
    T2 = 1.5 * otsu_threshold  # Upper threshold
    # print(f"Computed Canny thresholds: {T1:.2f}, {T2:.2f}")
    return int(T1), int(T2)

def detect_edges(grayscale_image, processing_config):
    """
    Detects edges in a grayscale image using Canny edge detection.

    - Uses CUDA if `grayscale_image` is `cuda.GpuMat`.
    - Uses CPU functions if `grayscale_image` is a NumPy ndarray.

    Args:
        grayscale_image (GpuMat or ndarray): Input grayscale image.
        processing_config (dict): Configuration dictionary.

    Returns:
        GpuMat or ndarray: Binary edge-detected image (same type as input).
    """
    # debug_mode = processing_config.get("Debug_Mode", False)
    cuda_enabled = processing_config.get("CUDA_Enabled", False)

    canny_thresholds = compute_canny_thresholds(grayscale_image, processing_config)

    if cuda_enabled and isinstance(grayscale_image, cuda.GpuMat):
        # Apply Canny edge detection on GPU
        gpu_canny = cv2.cuda.createCannyEdgeDetector(*canny_thresholds, L2gradient=True)
        edges = gpu_canny.detect(grayscale_image)  # Keeps processing in GPU

        return edges  # Returns GpuMat

    else:
        # Apply Canny edge detection on CPU
        edges = cv2.Canny(grayscale_image, canny_thresholds[0], canny_thresholds[1], L2gradient=True)

        return edges  # Returns ndarray

def old_detect_edges(grayscale_image, processing_config):
    """
    Detects noise using a Laplacian filter, applies Gaussian blurring if needed, and performs Canny edge detection.

    - Uses CUDA if `grayscale_image` is `cuda.GpuMat`.
    - Uses CPU functions if `grayscale_image` is a NumPy ndarray.

    Args:
        grayscale_image (GpuMat or ndarray): Input grayscale image.
        processing_config (dict): Configuration dictionary.

    Returns:
        GpuMat or ndarray: Binary edge-detected image (same type as input).
    """
    debug_mode = processing_config.get("Debug_Mode", False)
    cuda_enabled = processing_config.get("CUDA_Enabled", False)
    noise_threshold = processing_config.get("Noise_Threshold", 500)  # Adjust based on testing
    gaussian_kernel = processing_config.get("Gaussian_Kernel", (5, 5))  # Default Gaussian kernel size
    threshold_low, threshold_high = processing_config.get("Canny_Thresholds", (50, 150))

    if cuda_enabled and isinstance(grayscale_image, cuda.GpuMat):
        # ✅ Step 1: Compute Laplacian Variance (Noise Detection)
        gpu_image_conv = grayscale_image.convertTo(cv2.CV_32F, alpha=1.0, beta=0.0)
        gpu_laplacian = cv2.cuda.createLaplacianFilter(cv2.CV_32F, cv2.CV_32F, 3)
        gpu_laplacian_result = gpu_laplacian.apply(gpu_image_conv)

        gpu_mean_stddev = cv2.cuda.meanStdDev(gpu_laplacian_result)  # Compute mean & stddev
        # ✅ Download result
        mean_stddev = gpu_mean_stddev.download()

        # ✅ Extract standard deviation
        stddev = mean_stddev[0][1]
        variance = stddev**2  # Variance = (stddev)^2

        if debug_mode:
            print(f"📌 GPU Computed Laplacian Variance (Noise Level): {variance:.2f}")

        # ✅ Step 2: Apply Gaussian Blur if Noise is Excessive
        if variance > noise_threshold:
            print("⚠️ High noise detected → Applying Gaussian Blur before edge detection.")
            gpu_gaussian = cv2.cuda.createGaussianFilter(cv2.CV_8U, cv2.CV_8U, gaussian_kernel, 0)
            grayscale_image = gpu_gaussian.apply(grayscale_image)  # ✅ Blur the image before Canny

        # ✅ Step 3: Apply Canny Edge Detection
        gpu_canny = cv2.cuda.createCannyEdgeDetector(threshold_low, threshold_high)
        edges = gpu_canny.detect(grayscale_image)  # ✅ Keeps processing in GPU

        return edges  # ✅ Returns GpuMat

    else:
        # ✅ Step 1: Compute Laplacian Variance on CPU
        laplacian = cv2.Laplacian(grayscale_image, cv2.CV_16S, ksize=5)
        mean_stddev = cv2.meanStdDev(laplacian)
        stddev = mean_stddev[1]
        variance = stddev[0][0]**2

        if debug_mode:
            print(f"📌 CPU Computed Laplacian Variance (Noise Level): {variance:.2f}")

        # ✅ Step 2: Apply Gaussian Blur if Noise is Excessive
        if variance > noise_threshold:
            print("⚠️ High noise detected → Applying Gaussian Blur before edge detection.")
            grayscale_image = cv2.GaussianBlur(grayscale_image, gaussian_kernel, 0)

        # ✅ Step 3: Apply Canny Edge Detection
        edges = cv2.Canny(grayscale_image, threshold_low, threshold_high)

        return edges # ✅ Returns ndarray

    # # Step 3: Dynamically calculate Canny thresholds
    # mean_intensity = np.mean(blurred)
    # threshold_low = max(30, int(mean_intensity * threshold_scale[0]))
    # threshold_high = min(255, int(mean_intensity * threshold_scale[1]))

    # # Step 4: Apply Canny edge detection
    # canny = cv2.Canny(blurred, threshold_low, threshold_high)

    # if debug_mode:
    #     # print(f"Smoothing Kernel: ({horizontal_smoothing_kernel}, {vertical_smoothing_kernel})")
    #     debug_path = processing_config.get("Debug_Output_Path", None)
    #     print(f"Mean Intensity: {mean_intensity}")
    #     print(f"Canny Thresholds: (Low: {threshold_low}, High: {threshold_high})")
    #     cv2.imwrite(os.path.join(debug_path, "blurred_gray.png"), blurred)
    #     cv2.imwrite(os.path.join(debug_path, "detected_edges.png"), canny)
    #     # debug

    # return canny

def compute_skew_angle(edges, i, processing_config, debug_data=None):
    """
    Computes the skew angle of vertical boundaries for a subphoto using Hough Line Transform,
    focusing on lines near the left and right boundary ranges.
    
    Parameters:
        edges (ndarray): Edge-detected image.
        i (int): Subphoto index for debug tracking.
        processing_config (dict): Configuration settings for Hough transform and skew detection.
        debug_data (DebugData): Object for storing debug information.
        margin_ratio (float): Ratio of subphoto width used for left and right boundary detection.
    
    Returns:
        float: Skew angle in degrees.
    """
    debug_mode = processing_config.get("Debug_Mode", False)
    skew_roi_margin = processing_config.get("Skew_ROI_Margin", 0.05)
    # hough_threshold = config.get("Hough_Threshold", 100)

    # Step 1️⃣: Get the width of the subphoto
    subphoto_width = edges.shape[1]
    subphoto_height = edges.shape[0]

    hough_threshold = int(subphoto_height * 0.25)

    # Step 2️⃣: Define margins for left and right boundary detection
    margin = int(subphoto_width * skew_roi_margin)
    left_boundary_range = edges[:, 0:margin]
    right_boundary_range = edges[:, subphoto_width - margin:]

    # Step 3️⃣: Initialize list for detected lines
    lines = []

    rho_resolution = 1
    # theta_resolution = np.pi / 360
    theta_resolution = np.deg2rad(0.05) 
    min_theta = np.deg2rad(-10)
    max_theta = np.deg2rad(10)

    # Step 4️⃣: Detect vertical lines near the left boundary
    left_lines = cv2.HoughLines(
        left_boundary_range,
        rho=rho_resolution,
        theta=theta_resolution,
        threshold=hough_threshold,
        min_theta=min_theta,  # Allow near-vertical lines
        max_theta=max_theta
    )
    if left_lines is not None:
        for line in left_lines:
            rho, theta = line[0]
            lines.append({
                "rho": rho,
                "theta": theta,
                "region": "left"
            })

    # Step 5️⃣: Detect vertical lines near the right boundary
    right_lines = cv2.HoughLines(
        right_boundary_range,
        rho=rho_resolution,
        theta=theta_resolution,
        threshold=hough_threshold,
        min_theta=min_theta,  # Allow near-vertical lines
        max_theta=max_theta
    )
    if right_lines is not None:
        for line in right_lines:
            rho, theta = line[0]
            # Adjust rho to account for the horizontal offset of the right boundary
            rho += (subphoto_width - margin) * np.cos(theta)
            lines.append({
                "rho": rho,
                "theta": theta,
                "region": "right"
            })

    # Step 6️⃣: Handle case where no lines are detected
    if not lines:
        print("No vertical lines detected; assuming 0° skew.")
        return 0  # No skew detected

    # Step 7️⃣: Directly compute the skew angle from the detected lines
    angles = [np.degrees(line["theta"]) for line in lines]
    # Skew angle relative to vertical (0° or 180°)
    # skew_angles = [angle if angle <= 90 else angle - 180 for angle in angles]
    median_angle = np.median(angles)

    print(f"Detected vertical skew angle: {median_angle:.2f}°")

    # 🔍 Store debug data for visualization
    if debug_mode and debug_data:
        # raw_subphoto = debug_data.raw_subphotos[i]
        debug_data.add_plot_data(f"detected_lines_subphoto_{i}", {
            "index": i,
            "lines": lines,
            "median_skew_angle": median_angle,
            # "raw_subphoto": raw_subphoto,
            "subphoto_width": subphoto_width,
            "margin": margin
        })

    return median_angle

def compute_horizontal_skew_angle(edges, i, config, debug_data=None, margin_ratio=0.05):
    """
    Computes the skew angle of horizontal boundaries for a subphoto by
    detecting lines separately in the top and bottom boundary ranges.
    Stores detected lines in debug_data for later visualization.
    """
    debug_mode = config.get("Debug_Mode", False)
    # hough_threshold = config.get("Hough_Threshold", 100)
    # skew_angle_threshold = config.get("Skew_Angle_Threshold", 10)

    # # 1️⃣ Get the height of the subphoto (edge region)
    # subphoto_height = edges.shape[0]

    # # 2️⃣ Define margins for detecting top and bottom boundary lines
    # margin = int(subphoto_height * margin_ratio)
    # top_boundary_range = edges[0:margin, :]
    # bottom_boundary_range = edges[subphoto_height - margin:, :]

    # # Initialize a list to store all detected lines (with metadata)
    # lines = []

    # min_theta = np.deg2rad(90 - skew_angle_threshold)
    # max_theta = np.deg2rad(90 + skew_angle_threshold)

    # # 3️⃣ Detect lines near the top boundary using Hough Line Transform
    # top_lines = cv2.HoughLines(
    #     top_boundary_range,
    #     rho=1,
    #     theta=np.pi / 180,
    #     threshold=hough_threshold,
    #     min_theta=min_theta,
    #     max_theta=max_theta
    # )
    # if top_lines is not None:
    #     for line in top_lines:
    #         rho, theta = line[0]
    #         # Store line with its region information
    #         lines.append({
    #             "rho": rho,
    #             "theta": theta - np.pi/2,  # Center around horizontal
    #             "region": "top"
    #         })

    # # 4️⃣ Detect lines near the bottom boundary using Hough Line Transform
    # bottom_lines = cv2.HoughLines(
    #     bottom_boundary_range,
    #     rho=1,
    #     theta=np.pi / 180,
    #     threshold=hough_threshold,
    #     min_theta=min_theta,
    #     max_theta=max_theta
    # )
    # if bottom_lines is not None:
    #     for line in bottom_lines:
    #         rho, theta = line[0]
    #         # Adjust rho to account for the vertical offset of the bottom boundary
    #         rho += (subphoto_height - margin) * np.sin(theta)
    #         lines.append({
    #             "rho": rho,
    #             "theta": theta - np.pi/2,  # Center around horizontal
    #             "region": "bottom"
    #         })

    # # 5️⃣ Handle cases where no lines were detected
    # if not lines:
    #     print("No lines detected; assuming 0° skew.")
    #     return 0  # No lines detected → Assume no skew

    # # Step 7️⃣: Directly compute the median skew angle from detected lines
    # angles = [line["theta"] for line in lines]
    # median_angle = np.rad2deg(np.median(angles) - np.pi/2)  # Convert to degrees and center around horizontal

    # # 8️⃣ Compute the median angle for skew correction
    # # median_angle = np.median(horizontal_angles)
    # print(f"Detected skew angle: {median_angle}°")

    # # 9️⃣ Store debug information for visualization
    # if debug_mode and debug_data:
    #     # raw_subphoto = debug_data.raw_subphotos[i]  # Get the raw subphoto from debug data
    #     debug_data.add_plot_data(f"detected_lines_subphoto_{i}", {
    #         "index": i,
    #         "lines": lines,
    #         "median_skew_angle": median_angle,
    #         # "raw_subphoto": raw_subphoto,  # Add the raw subphoto for overlay
    #         "subphoto_height": subphoto_height,
    #         "margin": margin
    #     })

    # return median_angle

def correct_skew(image, angle, processing_config):
    """
    Rotates an image to correct skew based on the given angle.

    Parameters:
        image (ndarray): Input image.
        angle (float): Skew angle in degrees.

    Returns:
        ndarray: Skew-corrected image.
    """
    if image is None or image.size == 0:
        raise ValueError("Invalid image provided to correct_skew.")

    h, w = image.shape[:2]
    if h == 0 or w == 0:
        raise ValueError(f"Image has invalid dimensions: height={h}, width={w}")

    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, scale=1.0)
    return cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)

def detect_horizontal_boundaries_cuda(edges, processing_config, debug_data=None):
    """
    Detect horizontal boundaries in an edge-detected image using CUDA HoughLinesDetector.

    Args:
        edges (cuda.GpuMat or ndarray): Edge-detected image.
        processing_config (dict): Configuration settings.
        debug_data (DebugData): Optional debug data object.

    Returns:
        list: List of detected horizontal boundary row indices.
    """
    debug_mode = processing_config.get("Debug_Mode", False)
    hough_threshold = processing_config.get("Hough_Threshold", 150)
    max_scanned_photos = processing_config.get("Max_Scanned_Photos", 6)
    min_theta = np.deg2rad(80)  # Focus around horizontal
    max_theta = np.deg2rad(100)

    # Ensure edges are on GPU
    if not isinstance(edges, cuda.GpuMat):
        edges_gpu = cuda.GpuMat()
        edges_gpu.upload(edges)
    else:
        edges_gpu = edges

    # Create CUDA HoughLinesDetector
    hough_detector = cv2.cuda.createHoughLinesDetector(
        rho=1,
        theta=np.pi / 180,
        threshold=300,
        doSort=True,
        maxLines=max_scanned_photos-1
    )

    # Detect lines (output is GpuMat Nx1x2)
    lines_gpu = hough_detector.detect(edges_gpu)
    lines = lines_gpu.download() if lines_gpu is not None else np.empty((0, 1, 2))

    if debug_mode:
        print(f"CUDA HoughLines detected {len(lines)} lines.")

    boundary_rows = []

    for line in lines:
        rho, theta = line[0]
        sin_theta = np.sin(theta)

        if debug_mode:
            print(f"Line detected: rho={rho:.2f}, theta={theta:.2f}")

        if abs(sin_theta) > 1e-6:  # Avoid division by zero
            y = rho / sin_theta
            y_int = int(round(y))
            if debug_mode:
                print(f"Calculated y-coordinate: {y:.2f} (rounded to {y_int})")

            if 0 <= y_int < edges_gpu.size()[0]:  # Valid row index
                boundary_rows.append(y_int)
                if debug_mode:
                    print(f"Detected line at y={y_int} (rho={rho:.2f}, theta={theta:.2f})")

    # Deduplicate close detections
    boundary_rows = sorted(boundary_rows)
    filtered_rows = []
    min_spacing = int(edges_gpu.size()[0] / (processing_config.get("Max_Scanned_Photos", 6) * 2))  # dynamic tolerance

    last_y = -min_spacing
    for y in boundary_rows:
        if abs(y - last_y) >= min_spacing:
            filtered_rows.append(y)
            last_y = y

    if debug_mode:
        print(f"Filtered boundaries: {filtered_rows}")
        if debug_data:
            debug_data.add_plot_data("cuda_hough_boundaries", {
                "raw_rows": boundary_rows,
                "filtered_rows": filtered_rows
            })

    return filtered_rows

def detect_horizontal_boundaries(edges, processing_config, debug_data=None):
    """
    Detect horizontal boundaries in an edge-detected image, exaggerating peaks in the smoothed projection.

    Args:
        edges (numpy.ndarray): Edge-detected binary image (values 0 or 255).
        processing_config (dict): Configuration dictionary with parameters:
            - "Projection_Smoothing_Sigma" (int): Smoothing sigma for Gaussian filter.
            - "Threshold_Std_Scale" (float): Multiplier for dynamic threshold based on smoothed values.
            - "Peak_Exaggeration_Method" (str): Method to exaggerate peaks ('power', 'log', or None).
            - "Peak_Exaggeration_Factor" (float): Factor to control exaggeration strength (e.g., power or log base).
            - "Max_Scanned_Photos" (int): Maximum number of stacked photos (affects min boundary spacing).
            - "Debug_Mode" (bool): If True, saves debugging plots.
            - "Debug_Output_Path" (str): File path to save debug plots (default: "horizontal_boundaries.png").

    Returns:
        list: List of detected horizontal boundary row indices.
    """
    # Configurable parameters
    debug_mode = processing_config.get("Debug_Mode", False)
    cuda_enabled = processing_config.get("CUDA_Enabled", False)
    smoothing_sigma = processing_config.get("Projection_Smoothing_Sigma", 10)
    threshold_std_scale = processing_config.get("Threshold_Std_Scale", 2.0)
    peak_exaggeration_method = processing_config.get("Peak_Exaggeration_Method", None)
    peak_exaggeration_factor = processing_config.get("Peak_Exaggeration_Factor", 2.0)
    max_scanned_photos = processing_config.get("Max_Scanned_Photos", 6)

    if cuda_enabled and isinstance(edges, cuda.GpuMat):
        # Download the edge-detected image from GPU
        edges = edges.download()

    # Step 1: Compute row-wise projection (sum edge intensities for each row)
    projection = np.sum(edges, axis=1)

    # Step 2: Smooth the projection using a Gaussian filter
    smoothed_projection = gaussian_filter1d(projection, sigma=smoothing_sigma)

    # Step 3: Exaggerate peaks in the smoothed projection
    if peak_exaggeration_method == 'power':
        # Apply power scaling to exaggerate peaks
        exaggerated_projection = smoothed_projection**peak_exaggeration_factor
    elif peak_exaggeration_method == 'log':
        # Apply logarithmic scaling to exaggerate peaks (add small epsilon to avoid log(0))
        exaggerated_projection = np.log1p(smoothed_projection * peak_exaggeration_factor)
    else:
        # No exaggeration
        exaggerated_projection = smoothed_projection

    # Step 4: Calculate the dynamic threshold
    mean_projection = np.mean(exaggerated_projection)
    std_projection = np.std(exaggerated_projection)
    boundary_threshold = mean_projection + (threshold_std_scale * std_projection)

    # Step 5: Detect peaks using height and minimum spacing
    image_height = edges.shape[0]
    min_boundary_spacing = int((image_height / max_scanned_photos) * 0.75)
    peaks, _ = find_peaks(
        exaggerated_projection,
        height=boundary_threshold,
        distance=min_boundary_spacing
    )

    # Step 6: Filter out boundaries too close to the top or bottom
    boundaries = [p for p in peaks if min_boundary_spacing <= p <= (image_height - min_boundary_spacing)]

    if debug_mode:
        # Store the raw data for plotting later
        debug_data.add_plot_data("horizontal_boundaries_plot", {
            "smoothed_projection": smoothed_projection,
            "exaggerated_projection": exaggerated_projection,
            "boundary_threshold": boundary_threshold,
            "boundaries": boundaries
        })

    return boundaries

def detect_whitespace_bounds(image_or_edges, processing_config, debug_data=None):
    """
    Detects the left and right content bounds of an image by analyzing edge density.

    Parameters:
        edges (ndarray): Edge-detected image.
        processing_config (dict): Configuration with "Content_Threshold_Ratio".

    Returns:
        tuple: (left_bound, right_bound) indices for cropping.
    """
    debug_mode = processing_config.get("Debug_Mode", False)
    # Ensure we are operating on edges; if a color or grayscale image was provided, compute edges first
    edges = image_or_edges
    try:
        if edges is None:
            raise ValueError("No image provided for whitespace detection")
        # If 3-channel or not 2D, convert and edge-detect
        if len(edges.shape) == 3:
            gray = cv2.cvtColor(edges, cv2.COLOR_BGR2GRAY)
            t1, t2 = compute_canny_thresholds(gray, processing_config)
            edges = cv2.Canny(gray, t1, t2, L2gradient=True)
        elif edges.dtype != np.uint8 or edges.max() > 1 and edges.max() <= 255 and np.unique(edges).size > 2:
            # Likely grayscale image, compute edges
            t1, t2 = compute_canny_thresholds(edges, processing_config)
            edges = cv2.Canny(edges, t1, t2, L2gradient=True)
    except Exception:
        # Fallback: attempt to treat input as already-edged
        pass

    # Step 1: Sum edge intensities along columns
    column_sums = np.sum(edges, axis=0)

    # Step 2: Smooth the column sums to reduce noise
    # smoothed_sums = cv2.GaussianBlur(column_sums, (15, 1), 0)

    # Step 3: Calculate a dynamic threshold for content
    content_threshold_ratio = processing_config.get("Content_Threshold_Ratio", 0.05)
    # threshold = smoothed_sums.max() * content_threshold_ratio
    threshold = column_sums.max() * content_threshold_ratio


    # Step 4: Identify columns that exceed the threshold
    # non_whitespace_indices = np.where(smoothed_sums > threshold)[0]
    non_whitespace_indices = np.where(column_sums > threshold)[0]

    if debug_mode and debug_data is not None:
        # Store the raw data for plotting later
        debug_data.add_plot_data("whitespace_detection_plot", {
            "column_sums": column_sums,
            "threshold": threshold,
            "non_whitespace_indices": non_whitespace_indices
        })

    # Step 5: Handle cases with no detected content
    if non_whitespace_indices.size == 0:
        return 0, edges.shape[1]  # Default to full image width

    # Step 6: Return the bounds of the detected content
    return non_whitespace_indices[0], non_whitespace_indices[-1]

def process_subphoto(subphoto, edges_subregion, processing_config, i, debug_data=None):
    """
    Processes a single subphoto: detects and corrects skew, and crops dynamically.

    Parameters:
        subphoto (ndarray): Subphoto region.
        edges_subregion (ndarray): Edge-detected subphoto region.
        processing_config (dict): Configuration dictionary.

    Returns:
        ndarray: Cropped and skew-corrected subphoto.
    """
    # Compute skew angle from the provided edge subregion
    skew_angle = compute_skew_angle(edges_subregion, i, processing_config, debug_data)

    if subphoto is None or subphoto.size == 0:
        raise ValueError("Empty or invalid subphoto passed to correct_skew.")

    # Correct the skew for the subphoto
    corrected_subphoto = correct_skew(subphoto, skew_angle, processing_config)

    if debug_data:
        debug_data.add_intermediate_output(f"skew_angle_subphoto_{i}", skew_angle)
        debug_data.add_intermediate_output(f"skew_corrected_subphoto_{i}", corrected_subphoto)

    # Get the image dimensions
    height, width = corrected_subphoto.shape[:2]

    # Detect left and right bounds for cropping
    left, right = detect_whitespace_bounds(corrected_subphoto, processing_config, debug_data)

    left = max(0, left)
    right = min(width, right)

    # Calculate the dynamic crop margin based on skew angle
    min_margin = processing_config.get("Min_Crop_Margin", 10)
    margin_factor = processing_config.get("Crop_Margin_Factor", 8)  # 5° → 50 px

    # Convert skew angle to a margin
    adaptive_margin = min_margin + int(margin_factor * abs(skew_angle))
    adaptive_margin = min(adaptive_margin, processing_config.get("Max_Crop_Margin", 100))  # Cap at max margin

    # Apply dynamic cropping to the top and bottom
    top = adaptive_margin
    bottom = height - adaptive_margin

    # Ensure the crop bounds are within the image dimensions
    top = max(0, top)
    bottom = min(height, bottom)

    if debug_data:
        debug_data.add_intermediate_output(
            f"cropping_bounds_subphoto_{i}",
            {"left": left, "right": right, "top": top, "bottom": bottom}
        )

    # Return the cropped subphoto
    return corrected_subphoto[top:bottom, left:right]

#     _____       _ _ _                      _     _____                 
#    / ____|     | (_) |                    | |   / ____|                
#   | (___  _ __ | |_| |_     __ _ _ __   __| |  | |     _ __ ___  _ __  
#    \___ \| '_ \| | | __|   / _` | '_ \ / _` |  | |    | '__/ _ \| '_ \ 
#    ____) | |_) | | | |_   | (_| | | | | (_| |  | |____| | | (_) | |_) |
#   |_____/| .__/|_|_|\__|   \__,_|_| |_|\__,_|   \_____|_|  \___/| .__/ 
#          | |                                                    | |    
#          |_|                                                    |_|    
def split_and_crop(combined_image, processing_config):
    """
    Splits a combined image into subphotos, corrects skew, and crops dynamically.
    Detects processing errors and returns structured exceptions.

    Parameters:
        combined_image (ndarray): Combined input image.
        processing_config (dict): Configuration dictionary.

    Returns:
        list: List of cropped and skew-corrected subphotos.
        ErrorInfo or None: An error object if processing fails, otherwise None.
    """
    debug_mode = processing_config.get("Debug_Mode", False)
    cuda_enabled = processing_config.get("CUDA_Enabled", False)
    max_scanned_photos = processing_config.get("Max_Scanned_Photos", 6)

    if debug_mode:
        debug_data = DebugData()
        print(f"{combined_image.dtype} {combined_image.shape}")
        # debug_path = config.get("Debug_Output_Path", None)
    else:
        debug_data = None

    # Step 1: Convert the image to grayscale
    grayscale_image = convert_to_grayscale(combined_image, processing_config)

    # Detect edges
    edges = detect_edges(grayscale_image, processing_config)

    if edges is None or not np.any(edges):
        return [], ErrorInfo("EdgeDetectionFailure", "Edge detection failed."), debug_data
    
    # elif cuda_enabled and isinstance(grayscale_image, cuda.GpuMat):
    #     # Download the edge-detected image from GPU
    #     edges = edges.download()
    
    # Store the full edges image if in debug mode
    if debug_data is not None:
        debug_data.add_intermediate_output("full_edges", edges)

    # Detect horizontal boundaries
    if cuda_enabled:
        horizontal_boundaries = detect_horizontal_boundaries_cuda(edges, processing_config, debug_data)
        edges = edges.download()  # Download the edges for further processing
    else:
        horizontal_boundaries = detect_horizontal_boundaries(edges, processing_config, debug_data)


    # if horizontal_boundaries is None or len(horizontal_boundaries) == 0:
    #     print("No horizontal boundaries detected; attempting blur before Canny.")
    #     new_config = processing_config.copy()
    #     new_config["Blur_Before_Canny"] = True
    #     edges = detect_edges(combined_image, new_config)
    #     horizontal_boundaries = detect_horizontal_boundaries(edges, new_config, debug_data)

    if debug_data is not None:
        print(f"Detected boundaries: {horizontal_boundaries}")
        debug_data.add_detected_boundaries(horizontal_boundaries)

    # Add image bounds to ensure complete coverage
    all_boundaries = [0] + horizontal_boundaries + [combined_image.shape[0]]

    # **EARLY EXIT: Check if subphoto count exceeds Max_Scanned_Photos**
    num_subphotos = len(all_boundaries) - 1
    if num_subphotos > max_scanned_photos:
        return [], ErrorInfo("TooManySubphotos", f"{num_subphotos} subphotos detected, exceeding max of {max_scanned_photos}."), debug_data

    subphotos = []

    for i in range(num_subphotos):
        top, bottom = all_boundaries[i], all_boundaries[i + 1]
        subphoto = combined_image[top:bottom, :]
        edges_subregion = edges[top:bottom, :]

        if subphoto.shape[0] == 0 or subphoto.shape[1] == 0:
            print(f"Subphoto {i} has invalid dimensions: {subphoto.shape}")
            continue

        if debug_data is not None:
            debug_data.add_raw_subphoto(subphoto.copy())
            debug_data.add_edges_subregion(edges_subregion)
            # cv2.imwrite(os.path.join(debug_path, f"edges_subregion_{i}.png"), edges_subregion)

        try:
            processed_subphoto = process_subphoto(
                subphoto,
                edges_subregion,
                processing_config,
                i,
                debug_data
                )
            subphotos.append(processed_subphoto)
        except ValueError as e:
            print(f"Error processing subphoto {i}: {e}")
            return [], ErrorInfo("SubphotoProcessingFailure", str(e)), debug_data

    if len(subphotos) == 0:
        return [], ErrorInfo("NoSubphotosExtracted", "No valid subphotos were processed."), debug_data

    return subphotos, None, debug_data  # No errors

def ensure_permissions(file_path):
    try:
        os.chmod(file_path, 0o644)  # Grant read and write permissions for the owner, read for others
    except Exception as e:
        print(f"Failed to set permissions for {file_path}: {e}")

def create_temp_copy(file_path):
    """
    Creates a temporary copy of the given file one level up from its directory.

    Parameters:
        file_path (str): Path to the original file.

    Returns:
        str: Path to the temporary file.
    """
    # Get the parent directory (one level up)
    original_dir = os.path.dirname(file_path)  # Directory of the original file
    parent_dir = os.path.dirname(original_dir)  # Move one level up

    # Construct the temporary file name and path
    temp_file_name = os.path.splitext(os.path.basename(file_path))[0] + "_temp.tiff"
    temp_file_path = os.path.join(parent_dir, temp_file_name)

    # Copy the original file to the temporary path
    shutil.copy(file_path, temp_file_path)
    print(f"Temporary copy created: {temp_file_path}")

    return temp_file_path

def inject_metadata(file_path, exif_date, description):
    """
    Injects metadata into the file using ExifTool.

    Parameters:
        file_path (str): Path to the file.
        exif_date (str): Date in EXIF format (YYYY:MM:DD HH:MM:SS).
        description (str): Description to be added to the metadata.
    """
    try:
        cmd = [
            "exiftool",
            "-overwrite_original",
            f"-AllDates={exif_date}",
            f"-XMP:Description={description}",
            f"-XMP-dc:Title={description}",
            f"-IPTC:ObjectName={description}",
            f"-IPTC:Caption-Abstract={description}",
            file_path
        ]
        subprocess.run(cmd, check=True)
        # print(f"Metadata injected into {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error injecting metadata into {file_path}: {e}")
    except FileNotFoundError:
        # exiftool is not installed or not on PATH; continue without metadata
        print("ExifTool not found on PATH; skipping metadata injection.")

def save_and_inject_metadata(photo, output_base_folder, base_name, part_number, exif_date, description, year, saving_config):
    """
    Saves a photo in multiple formats based on configuration settings and injects metadata.

    Args:
        photo (ndarray): The image to save.
        output_base_folder (str): The base folder for saving images.
        base_name (str): The base name for the files.
        part_number (int): The part number of the photo.
        exif_date (str): The EXIF date format (YYYY:MM:DD HH:MM:SS).
        description (str): The image description.
        year (str): The year for organizing folders.
        config (dict): Configuration settings including format preferences.
    """
    # File format options and their respective save functions
    format_settings = {
        "HEIC": {
            "enabled": saving_config.get("Save_As_HEIC", False),
            "folder": os.path.join(output_base_folder, "HEIC", year),
            "extension": "heic",
        },
        "JPEG": {
            "enabled": saving_config.get("Save_As_JPEG", False),
            "folder": os.path.join(output_base_folder, "JPEG", year),
            "extension": "jpg",
        },
        "PNG": {
            "enabled": saving_config.get("Save_As_PNG", False),
            "folder": os.path.join(output_base_folder, "PNG", year),
            "extension": "png",
        },
        "TIFF": {
            "enabled": saving_config.get("Save_As_TIFF", False),
            "folder": os.path.join(output_base_folder, "TIFF", year),
            "extension": "tiff",
        },
    }

    # Format the filename
    formatted_date = exif_date.split(" ")[0].replace(":", "_")  # YYYY_MM_DD
    file_name = f"{formatted_date}_{base_name}_pt_{part_number}"

    # Process each format
    for format_name, settings in format_settings.items():
        if settings["enabled"]:
            # Ensure the folder exists **only if this format is enabled**
            os.makedirs(settings["folder"], exist_ok=True)

            file_path = os.path.join(settings["folder"], f"{file_name}.{settings['extension']}")

            # **Use Pillow-HEIF for HEIC**
            if format_name == "HEIC":
                pil_img = Image.fromarray(cv2.cvtColor(photo, cv2.COLOR_BGR2RGB))  # Convert for Pillow
                heif_file = pillow_heif.from_pillow(pil_img)
                heif_file.save(file_path, quality=saving_config.get("HEIC_Quality", 100))

            # **Use OpenCV for all other formats**
            else:
                save_params = []
                if format_name == "JPEG":
                    save_params = [cv2.IMWRITE_JPEG_QUALITY, saving_config.get("JPEG_Quality", 100)]
                cv2.imwrite(file_path, photo, save_params)

            # Inject metadata
            inject_metadata(file_path, exif_date, description)
            print(f"Saved {format_name}: {file_path}")

# def compute_skew_angle(edges, i, config, debug_data=None, margin_ratio=0.1):
#     """
#     Computes the skew angle of horizontal boundaries for a subphoto, focusing
#     only on lines near the top or bottom edges.

#     Parameters:
#         edges (ndarray): Edge-detected image.
#         margin_ratio (float): Proportion of height to consider as margin for top/bottom detection.

#     Returns:
#         float: Skew angle in degrees, focusing on top/bottom boundary lines.
#     """
#     debug_mode = config.get("Debug_Mode", False)
#     hough_threshold = config.get("Hough_Threshhold", 100)

#     # Determine the height of the subphoto from the edges array
#     subphoto_height = edges.shape[0]  # Number of rows corresponds to height

#     lines = []

#     # Define margins for top and bottom boundary detection
#     margin = int(subphoto_height * margin_ratio)
#     top_boundary_range = (0, margin)  # Top margin
#     bottom_boundary_range = (subphoto_height - margin, subphoto_height)  # Bottom margin

#     # Detect lines using the Hough Line Transform
#     lines = cv2.HoughLines(edges, rho=1, theta=np.pi / 180, threshold=hough_threshold)

#     if lines is None:
#         print("No lines detected, assuming 0 skew")
#         return 0  # No lines detected, assume no skew

#     # Extract and filter horizontal lines near the top/bottom boundaries
#     horizontal_angles = []
#     for line in lines:
#         rho, theta = line[0]
#         angle = np.degrees(theta) - 90  # Convert to degrees and center around horizontal

#         # Check if the line is horizontal (-5° to 5°) and near the boundaries
#         if -10 <= angle <= 10:
#             # Calculate the line's y-position using rho
#             a = np.cos(theta)
#             b = np.sin(theta)
#             y_position = abs(rho * b)  # Absolute y-position of the line

#             # Include only lines near the top or bottom boundary
#             if (top_boundary_range[0] <= y_position <= top_boundary_range[1] or
#                     bottom_boundary_range[0] <= y_position <= bottom_boundary_range[1]):
#                 horizontal_angles.append(angle)

#     if not horizontal_angles:
#         print("No horizontal lines found in skew angle computation")
#         return 0  # No valid horizontal boundary lines detected

#     # Compute the median angle of horizontal boundary lines
#     median_angle = np.median(horizontal_angles)
#     print(f"Detected boundary skew angle: {median_angle}")

#     if debug_mode:
#         debug_data

#     return median_angle

# def visualize_detected_lines(edges, lines, i, config):
#     """
#     Visualizes the detected lines on the edges image and saves the visualization.

#     Args:
#         edges (numpy.ndarray): The edges array (input image).
#         lines (numpy.ndarray): Detected lines in the format output by Hough transform.
#         output_path (str): Path to save the visualized image.
#     """
#     # Convert the edges image to a BGR image for color line overlay
#     edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
#     # Check if any lines are detected
#     if lines is not None:
#         for line in lines:
#             rho, theta = line[0]  # Extract rho and theta
#             # Compute the endpoints of the line for visualization
#             a = np.cos(theta)
#             b = np.sin(theta)
#             x0 = a * rho
#             y0 = b * rho
#             # Define the line length to draw
#             line_length = 1000
#             x1 = int(x0 + line_length * (-b))
#             y1 = int(y0 + line_length * a)
#             x2 = int(x0 - line_length * (-b))
#             y2 = int(y0 - line_length * a)
#             # Draw the line on the colored edges image
#             cv2.line(edges_colored, (x1, y1), (x2, y2), (0, 255, 0), 2)
#     else:
#         print("No lines were detected.")

#     # Save the visualized image
#     # cv2.imwrite(f"detected_lines_{i}.png", edges_colored)
#     debug_path = config.get("Debug_Output_Path", None)
#     cv2.imwrite(os.path.join(debug_path, f"detected_lines_{i}.png"), edges_colored)
#     # print(f"Visualization saved to {output_path}")