# processing.py

import cv2
from cv2 import cuda
import numpy as np
from CDT_config import CornerDetectionConfig
import copy

class CornerDetector:
    def __init__(self, config: CornerDetectionConfig):
        self.config = config
        self._init_cuda_resources() if self.config.CUDA_ENABLED else None

    def _init_cuda_resources(self):
        ksize, sigma_x, sigma_y = self.config.to_blur_tuple()
        self.cuda_blur = cuda.createGaussianFilter(
            srcType=cv2.CV_8UC1,
            dstType=cv2.CV_8UC1,
            ksize=ksize,
            sigma1=sigma_x,
            sigma2=sigma_y
        )

        self.cuda_canny = cuda.createCannyEdgeDetector(
            low_thresh=100,
            high_thresh=200,
            L2gradient=True
        )

        init_morph_args = self.config.morph_config
        self.cuda_morph = cuda.createMorphologyFilter(
            # op=self.config.morph_config["op"],
            op=cv2.MORPH_CLOSE,
            # srcType=self.config.morph_config["srcType"],
            srcType=cv2.CV_8UC1,
            kernel=cv2.getStructuringElement(
                cv2.MORPH_RECT,
                (init_morph_args["morph_kernel_w"], init_morph_args["morph_kernel_w"])
            ),
            iterations=init_morph_args["iterations"]
        )

        init_hough_args = self.config.hough_config
        self.cuda_hough = cuda.createHoughSegmentDetector(
            rho=init_hough_args["rho"],
            theta=init_hough_args["theta"],
            minLineLength=init_hough_args["minLineLength"],
            maxLineGap=init_hough_args["maxLineGap"],
            maxLines=init_hough_args["maxLines"],
            threshold=init_hough_args["threshold"]
        )

    def reconfigure(self, new_config: CornerDetectionConfig):
        """
        Efficiently updates the detector and blur filter only if needed.
        Uses setMaxCorners/setMinDistance when possible.
        """
        # print(f"[DEBUG] Reconfiguring with: {new_config.to_dict()}")
        self.config = new_config
        # print(f"[DEBUG] Cuda state: {self.config.CUDA_ENABLED}")
        # print(f"[DEBUG] Single photo state: {self.config.SINGLE_PHOTO}")

        # Check and update blur filter
        blur_args = self.config.to_blur_tuple()
        if not hasattr(self, "_last_blur_args") or blur_args != self._last_blur_args:
            print(f"[reconfigure] Blur args: {blur_args}")
            if self.config.CUDA_ENABLED:
                self.cuda_blur = cuda.createGaussianFilter(
                    srcType=cv2.CV_8UC1,
                    dstType=cv2.CV_8UC1,
                    ksize=blur_args[0],
                    sigma1=blur_args[1],
                    sigma2=blur_args[2]
                )
            self._last_blur_args = copy.deepcopy(blur_args)

        morph_args = self.config.morph_config
        if not hasattr(self, "_last_morph_args") or morph_args != self._last_morph_args:
            print(f"[reconfigure] Morph args: {morph_args}")
            if self.config.CUDA_ENABLED:
                print(f"[reconfigure] Recreating CUDA morphology filter with args: {morph_args}")
                self.cuda_morph = cuda.createMorphologyFilter(
                    op=cv2.MORPH_CLOSE,
                    srcType=cv2.CV_8UC1,
                    kernel=cv2.getStructuringElement(
                        cv2.MORPH_RECT,
                        (morph_args["morph_kernel_w"], morph_args["morph_kernel_w"])
                    ),
                    iterations=morph_args["iterations"]
                )
            self._last_morph_args = copy.deepcopy(morph_args)

        if self.config.CUDA_ENABLED:
            canny_args = self.config.canny_config
            self.cuda_canny.setLowThreshold(canny_args["lowThreshold"])
            self.cuda_canny.setHighThreshold(canny_args["highThreshold"])
            self.cuda_canny.setAppertureSize(canny_args["kernel_size"])
            self.cuda_canny.setL2Gradient(canny_args["L2gradient"])

            hough_args = self.config.hough_config
            self.cuda_hough.setRho(hough_args["rho"])
            self.cuda_hough.setTheta(hough_args["theta"])
            self.cuda_hough.setMinLineLength(hough_args["minLineLength"])
            self.cuda_hough.setMaxLineGap(hough_args["maxLineGap"])
            self.cuda_hough.setMaxLines(hough_args["maxLines"])
            self.cuda_hough.setThreshold(hough_args["threshold"])

            # print(f"[reconfigure] CUDA resources reconfigured with: {self.config.to_dict()}")

    def convert_to_grayscale(self, image):
        if self.config.CUDA_ENABLED:
            gpu_img = cuda.GpuMat()
            gpu_img.upload(image)
            return cuda.cvtColor(gpu_img, cv2.COLOR_BGR2GRAY)
        else:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def apply_blur(self, gray_image):
        if self.config.CUDA_ENABLED:
            if isinstance(gray_image, np.ndarray):
                gpu_img = cuda.GpuMat()
                gpu_img.upload(gray_image)
                return self.cuda_blur.apply(gpu_img)
            else:
                return self.cuda_blur.apply(gray_image)
        else:
            ksize, sigma_x, _ = self.config.to_blur_tuple()
            return cv2.GaussianBlur(gray_image, ksize, sigma_x)
        
    def apply_canny(self, blurred_gray):
        if self.config.CUDA_ENABLED:
            if isinstance(blurred_gray, np.ndarray):
                gpu_img = cuda.GpuMat()
                gpu_img.upload(blurred_gray)
            else:
                gpu_img = blurred_gray

            return self.cuda_canny.detect(gpu_img)
        else:
            canny_args = self.config.canny_config
            return cv2.Canny(
                blurred_gray,
                threshold1=canny_args.get("lowThreshold", 50),
                threshold2=canny_args.get("highThreshold", 150),
                apertureSize=canny_args.get("kernel_size", 3),
                L2gradient=canny_args.get("L2gradient", True)
            )
    
    def apply_morphology(self, canny_edges):
        print(f"[apply_morphology] morph_args: {self.config.morph_config}")
        if self.config.CUDA_ENABLED:
            if isinstance(canny_edges, np.ndarray):
                gpu_img = cuda.GpuMat()
                gpu_img.upload(canny_edges)
            else:
                gpu_img = canny_edges

            return self.cuda_morph.apply(gpu_img)
        else:
            morph_args = self.config.morph_config
            kernel = cv2.getStructuringElement(
                morph_args["op"],
                (morph_args["morph_kernel_w"], morph_args["morph_kernel_w"]),
            )
            return cv2.morphologyEx(
                canny_edges,
                morph_args["op"], kernel,
                iterations=morph_args["iterations"]
            )

    def detect_lines(self, canny_edges):
        if self.config.CUDA_ENABLED:
            if isinstance(canny_edges, np.ndarray):
                gpu_img = cuda.GpuMat()
                gpu_img.upload(canny_edges)
            else:
                gpu_img = canny_edges

            lines_gpu = self.cuda_hough.detect(gpu_img)
            if lines_gpu is not None and not lines_gpu.empty() and lines_gpu.size()[0] > 0:
                lines = [tuple(map(int, line)) for line in lines_gpu.download().reshape(-1, 4)]
            else:
                lines = []

        else:
            hough_args = self.config.hough_config
            lines_cpu = cv2.HoughLinesP(
                canny_edges,
                rho=hough_args["rho"],
                theta=hough_args["theta"],
                threshold=hough_args["threshold"],
                minLineLength=hough_args["minLineLength"],
                maxLineGap=hough_args["maxLineGap"]
            )
            if lines_cpu is not None:
                # Convert to list of tuples
                lines = [tuple(map(int, line[0])) for line in lines_cpu]
            else:
                lines = []

        # print(f"[detect_lines] CUDA lines: {lines}")
        return lines

    def filter_lines(self, lines, angle_tolerance=15):
        """
        Filters lines non-vertical/horizontal lines based on angle tolerance.
        """
        filtered_lines = []
        if lines is None:
            print("[filter_lines] No lines detected.")
            return filtered_lines

        for line in lines:
            x1, y1, x2, y2 = line
            angle = int(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            # print(f"[filter_lines] Line: {line} Angle: {angle} degrees")

            # angle = np.degrees(angle)

            if abs(angle) < angle_tolerance or abs(angle - 180) < angle_tolerance:
                filtered_lines.append(line)
                # print(f"[filter_lines] Line {line} is horizontal with angle {angle:.2f}")
                # print(f"[filter_lines] horizontal with angle {angle:.2f}")
            elif abs(angle - 90) < angle_tolerance or abs(angle + 90) < angle_tolerance:
                filtered_lines.append(line)
                # print(f"[filter_lines] Line {line} is vertical with angle {angle:.2f}")
                # print(f"[filter_lines] vertical")

        # print(f"[filter_lines] Filtered lines: {filtered_lines}")
        return filtered_lines
        