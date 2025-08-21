# visualizer.py

import cv2
import numpy as np

def draw_corners(image, corners, radius=8, thickness=2, font_scale=2.0):
    """
    Draws indexed and labeled corners with distinct colors.

    Args:
        image (np.ndarray): Original image (BGR).
        corners (list of tuples): List of corner coordinates (x, y).
        radius (int): Circle radius.
        thickness (int): Circle thickness (-1 = filled).
        font_scale (float): Font scale for corner annotations.

    Returns:
        np.ndarray: Annotated image.
    """
    if image is None or corners is None or len(corners) == 0:
        return image.copy()

    image_with_corners = image.copy()

    # Cycle of distinguishable BGR colors
    colors = [
        (0, 255, 0),     # green
        (255, 0, 0),     # blue
        (0, 0, 255),     # red
        (255, 255, 0),   # cyan
        (255, 0, 255),   # magenta
        (0, 255, 255),   # yellow
        (128, 0, 255),   # purple
        (255, 128, 0),   # orange
    ]

    for i, (x, y) in enumerate(corners):
        color = colors[i % len(colors)]

        # Draw circle at corner
        cv2.circle(image_with_corners, (x, y), radius, color, thickness)

        # Create label: index + coordinates
        label = f"{i+1}: ({x}, {y})"
        cv2.putText(image_with_corners, label, (x + radius + 5, y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 1, cv2.LINE_AA)
        
    return image_with_corners

def draw_lines(image, lines, color=(0, 255, 0), thickness=2):
    """
    Draws lines on the image.

    Args:
        image (np.ndarray): Original image (BGR).
        lines (list of tuples): List of lines defined by endpoints (x1, y1, x2, y2).
        color (tuple): BGR color for the lines.
        thickness (int): Line thickness.

    Returns:
        np.ndarray: Annotated image.
    """
    if isinstance(image, cv2.cuda.GpuMat):
        cpu_image = image.download()
        print("[draw_lines] Image is a GpuMat, converting to CPU image.")
        print(f"[draw_lines] Image shape: {cpu_image.shape}\n")
    else:
        cpu_image = image

    if cpu_image is None or lines is None or len(lines) == 0:
        return cpu_image.copy()

    if len(cpu_image.shape) == 2:
        # Convert to BGR if the image is grayscale
        cpu_image = cv2.cvtColor(cpu_image, cv2.COLOR_GRAY2BGR)
    
    image_with_lines = cpu_image.copy()

    for line in lines:
        x1, y1, x2, y2 = line
        cv2.line(image_with_lines, (x1, y1), (x2, y2), color, thickness)

    return image_with_lines
