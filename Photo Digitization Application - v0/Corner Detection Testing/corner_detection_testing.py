    

        # goodFeaturesToTrack detector settings
        self.GFTT_config = {
            "maxCorners": 4,
            "qualityLevel": 0.10,
            "minDistance": 0.0,
            "blockSize": 7,
            "useHarrisDetector": True,
            "harris_k": 0.001,
            "blur_before_detection": True  # previously Apply_Blur
        }

    def show_harris_map(self):
        print(f"[INFO] DISPLAYING HARRIS MAP")
        if self.response_image is not None:
            # Convert to BGR for OpenCV
            self.response_image = cv2.cvtColor(self.response_image, cv2.COLOR_GRAY2BGR)
            self.display_image(self.response_image)
            self.status_label.config(text="Harris map displayed.")
        else:
            print("[WARN] No response image to display.")
            return
        
    def to_gftt_args(self):
        """
        Returns the GFTT detector arguments for OpenCV.
        """
        gc = self.GFTT_config
        if self.CUDA_ENABLED:
            return {
                "maxCorners": gc["maxCorners"],
                "qualityLevel": gc["qualityLevel"],
                "minDistance": gc["minDistance"],
                "blockSize": gc["blockSize"],
                "useHarrisDetector": gc["useHarrisDetector"],
                "harrisK": gc["harris_k"]
            }
        else:
            return {
                "maxCorners": gc["maxCorners"],
                "qualityLevel": gc["qualityLevel"],
                "minDistance": gc["minDistance"],
                "blockSize": gc["blockSize"],
                "useHarrisDetector": gc["useHarrisDetector"],
                "k": gc["harris_k"]
            }



def detect_corners(self, image):
        gray = self.convert_to_grayscale(image)
        if self.config.GFTT_config.get("blur_before_detection", False):
            gray = self.apply_blur(gray)

        if self.config.CUDA_ENABLED:
            if isinstance(gray, np.ndarray):
                gpu_gray = cuda.GpuMat()
                gpu_gray.upload(gray)
            else:
                gpu_gray = gray

            self.cuda_gftt.setMaxCorners(self.config.GFTT_config["maxCorners"])
            self.cuda_gftt.setMinDistance(self.config.GFTT_config["minDistance"])
            corners_gpu = self.cuda_gftt.detect(gpu_gray, mask=None)
            corners = corners_gpu.download().reshape(-1, 2)

            print(f"[DC] CUDA corners: {corners}")

        else:
            args = self.config.to_gftt_args()
            corners = cv2.goodFeaturesToTrack(
                gray,
                **args
            )
            if corners is not None:
                corners = corners.reshape(-1, 2)

            print(f"[DC] CPU corners: {corners}")

        return [tuple(map(int, pt)) for pt in corners] if corners is not None else []

    def create_quadrant_masks(self, width, height):
        # print(f"[CQM] Creating quadrant masks for image of size: {width}x{height}")
        quadrants = [
            (width // 2, width, 0, height // 2),        # Top Right
            (width // 2, width, height // 2, height),    # Bottom Right
            (0, width // 2, height // 2, height),       # Bottom Left
            (0, width // 2, 0, height // 2)            # Top Left
        ]

        masks = []
        # i = 0
        for x0, x1, y0, y1 in quadrants:
            # i += 1
            mask = np.zeros((height, width), dtype=np.uint8)
            mask[y0:y1, x0:x1] = 255
            masks.append(mask)
            # cv2.imwrite(f"mask{i}_{x0}_{y0}.png", mask)  # Debugging line

        return masks

    def detect_quadrant_corners(self, image):
        cv2.imwrite("input_image.bmp", image)  # Debugging line
        gray = self.convert_to_grayscale(image)
        self.cuda_gftt.setMaxCorners(1)
        self.cuda_gftt.setMinDistance(0.0)
        if self.config.GFTT_config.get("blur_before_detection", False):
            gray = self.apply_blur(gray)

        if self.config.CUDA_ENABLED:
            w, h = gray.size()
            print(f"[DQC] CUDA image size: {w}x{h}")
        else:
            h, w = gray.shape[:2]
            print(f"[DQC] CPU image size: {w}x{h}")

        masks_cpu = self.create_quadrant_masks(w, h)
        corners = []

        response_criteria = cv2.cuda.createHarrisCorner(
            srcType=gray.type(),
            blockSize=self.config.GFTT_config["blockSize"],
            ksize=7,  # aperture size for Sobel; GFTT doesn't use this directly
            k=self.config.GFTT_config["harris_k"]  # k value used if Harris
        )

        # canny = self.cuda_canny.detect(gray)
        # cv2.imshow("Canny Edges", canny.download())  # Debugging line
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        response_map_gpu = response_criteria.compute(gray)
        response_map = response_map_gpu.download()
        norm_response = cv2.normalize(response_map, None, 0, 255, cv2.NORM_MINMAX)
        response_image = norm_response.astype(np.uint8)
        # cv2.imshow("Response Map", response_image)
        # cv2.waitKey(0)
        cv2.destroyAllWindows()
        cv2.imwrite("response_image.bmp", response_image)  # Debugging line

        if self.config.CUDA_ENABLED:
            i = 0
            for mask_cpu in masks_cpu:
                # print(f"[SIZES]\nimage.shape {image.shape} image.dtype {image.dtype}\nmask_cpu.shape {mask_cpu.shape} mask_cpu.dtype {mask_cpu.dtype}")
                # cv2.imwrite(f"mask_cpu{i}.png", mask_cpu)  # Debugging line
                mask_gpu = cuda.GpuMat()
                mask_gpu.upload(mask_cpu)
                result = self.cuda_gftt.detect(gray, mask=mask_gpu)
                # cpu_result = result.download() if result is not None else None
                # print(f"[DQC] CUDA result {i}: {result.download() if result is not None else 'None'}")
                if result is not None and result.size()[0] > 0:
                    corner_tuple = tuple(map(int, result.download().reshape(-1, 2)[0]))
                    print(f"[DQC] CUDA result {i}: {corner_tuple}")
                    corners.append(corner_tuple)

                i += 1

            print(f"[DQC] CUDA corners: {corners}")

        else:
            args = self.config.to_gftt_args()
            for mask_cpu in masks_cpu:
                result = cv2.goodFeaturesToTrack(
                    gray,
                    mask=mask_cpu,
                    maxCorners=1,
                    **{k: v for k, v in args.items() if k != "maxCorners"}
                )
                if result is not None:
                    corner_tuple = tuple(map(int, result.reshape(-1, 2)[0]))
                    corners.append(corner_tuple)

            print(f"[DQC] CPU corners: {corners}")

        return corners, response_image

        args = self.config.to_gftt_args()
        self.cuda_gftt = cuda.createGoodFeaturesToTrackDetector(
            srcType=cv2.CV_8UC1,
            **args
        )
        
    def process_current_image(self):
        if self.current_image is None:
            return
        self.update_config()
        if self.config.SINGLE_PHOTO:
            print("[PCI]: Detecting corners in single photo mode.")
            corners, self.response_image = self.detector.detect_quadrant_corners(self.current_image)
        else:
            print(f"[PCI]: Detecting corners in multi-photo mode.")
            corners = self.detector.detect_corners(self.current_image)

        print(f"[PCI]: Corners {corners}")

        self.result = draw_corners(self.current_image, corners)
        # cv2.imwrite("Corners.jpg", self.result)
        # cv2.waitKey(0)
        self.display_image(self.result)
        self.status_label.config(text=f"{len(corners)} corners detected.")
        # # Determine what GFTT args changed
        # new_gftt_args = self.config.to_gftt_args()
        # recreate_detector = False

        # if not hasattr(self, "_last_gftt_args"):
        #     recreate_detector = True
        # else:
        #     for key, new_val in new_gftt_args.items():
        #         if key not in ("maxCorners", "minDistance"):
        #             if self._last_gftt_args.get(key) != new_val:
        #                 recreate_detector = True
        #                 break

        # if self.config.CUDA_ENABLED:
        #     if recreate_detector or not hasattr(self, "cuda_gftt"):
        #         # Full recreation
        #         print(f"[DEBUG] Fully recreating CUDA GFTT detector with args: {new_gftt_args}")
        #         self.cuda_gftt = cv2.cuda.createGoodFeaturesToTrackDetector(
        #             srcType=cv2.CV_8UC1,
        #             **new_gftt_args
        #         )
        #     else:
        #         # Partial update
        #         print(f"[DEBUG] Partially updating CUDA GFTT detector with args: {new_gftt_args}")
        #         if self._last_gftt_args["maxCorners"] != new_gftt_args["maxCorners"]:
        #             self.cuda_gftt.setMaxCorners(new_gftt_args["maxCorners"])
        #         if self._last_gftt_args["minDistance"] != new_gftt_args["minDistance"]:
        #             self.cuda_gftt.setMinDistance(new_gftt_args["minDistance"])

        # self._last_gftt_args = new_gftt_args