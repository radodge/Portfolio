import os
import time
import queue
from queue import Queue
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from legacy_processing_utils import *
from legacy_gui_utils import *

class CombinedPhoto:
    """
    A combined photo object is created for each photo that appears in the ingest folder.

    Args:
        base_name (str): Unique name for the photo batch.
        file_path (str): Path to the original combined image file.
        combined_image (ndarray): The original combined image.
        subphotos (list): List of processed subphotos (empty if processing failed).
        config (dict, optional): Configuration settings used for processing.
        debug_data (DebugData, optional): Debugging information collected during processing.
        error_message (str, optional): Error message if processing failed.
    """
    def __init__(
            self,
            base_name,
            file_path,
            combined_image,
            subphotos,
            config=None,
            debug_data=None,
            error_message=None
            ):
        self.base_name = base_name
        self.file_path = file_path
        self.combined_image = combined_image
        self.subphotos = subphotos
        self.num_subphotos = len(subphotos)
        self.current_index = 0  # Track which subphoto is being processed
        self.error_message = error_message  # Store error details for manual review

        # Only store debug data if debug mode is enabled
        if config and config.get("Debug_Mode", False):
            self.config = config
            self.debug_data = debug_data or {}

def split_and_enqueue_photos(combined_image_path, processing_config, photo_queue):
    """
    Splits an input combined image into sub-photos and enqueues them for processing.

    Args:
        combined_image_path (str): Path to the input combined image.
        processing_config (dict): Configuration settings for image splitting.
        photo_queue (Queue): Queue where processed Combined_Photo objects are added.
    """
    debug_mode = processing_config.get("Debug_Mode", False)

    # Load the image as a NumPy array
    combined_image = load_image_as_numpy_array(combined_image_path)

    if combined_image is None:
        print(f"Error: Failed to load {combined_image_path}. Skipping processing.")
        return  # No further processing needed
    
    result = split_and_crop(combined_image, processing_config)
    if isinstance(result, tuple) and len(result) == 3:
        subphotos, error_info, debug_data = result
    else:
        subphotos, error_info = result
        debug_data = None

    base_name = os.path.splitext(os.path.basename(combined_image_path))[0]

    # If an error occurs, store the issue for manual review
    if isinstance(error_info, ErrorInfo):

        if error_info.error_type == "TooManySubphotos":
            print(f"Processing error for {base_name}: {error_info.message}. Retrying with alternate configuration.")
            alternate_config = get_alternate_processing_config(processing_config, error_info.error_type)
            result = split_and_crop(combined_image, alternate_config)
            if isinstance(result, tuple) and len(result) == 3:
                subphotos, error_info, debug_data = result
            else:
                subphotos, error_info = result
                debug_data = None

        # If still an error (or any error), enqueue a placeholder CombinedPhoto for GUI review
        if isinstance(error_info, ErrorInfo):
            print(f"Processing error for {base_name}: {error_info}")
            combined_photo_data = CombinedPhoto(
                base_name=base_name,
                file_path=combined_image_path,
                combined_image=combined_image,
                subphotos=subphotos if subphotos else [],
                config=processing_config,
                debug_data=debug_data if debug_mode else None,
                error_message=error_info.message
            )
        else:
            combined_photo_data = CombinedPhoto(
                base_name=base_name,
                file_path=combined_image_path,
                combined_image=combined_image,
                subphotos=subphotos,
                config=processing_config,
                debug_data=debug_data if debug_mode else None,
                error_message=None
            )
    else:
        # Successfully processed image
        combined_photo_data = CombinedPhoto(
            base_name=base_name,
            file_path=combined_image_path,
            combined_image=combined_image,
            subphotos=subphotos,
            config=processing_config,
            debug_data=debug_data if debug_mode else None,
            error_message=None
        )

    # Add to the queue (automatically wakes the processing thread)
    photo_queue.put(combined_photo_data)
    print(f"Enqueued {combined_photo_data.num_subphotos} subphotos for {base_name}.")

def get_alternate_processing_config(default_config, error_type):
    """
    Generates an alternate configuration based on the detected processing error.

    Args:
        default_config (dict): The original configuration dictionary.
        error_type (str): The type of error encountered.

    Returns:
        dict: A modified configuration dictionary for reprocessing.
    """
    alternate_config = default_config.copy()

    if error_type == "TooManySubphotos":
        # Reduce sensitivity of boundary detection
        alternate_config["Threshold_Std_Scale"] *= 1.5
        alternate_config["Projection_Smoothing_Sigma"] += 2
        # alternate_config["Content_Threshold_Ratio"] *= 1.2  # Increase tolerance for detecting content

    elif error_type == "EdgeDetectionFailure":
        # Adjust Canny edge detection thresholds
        alternate_config["Canny_Thresholds"] = (
            max(30, default_config["Canny_Thresholds"][0] - 10),
            min(255, default_config["Canny_Thresholds"][1] - 10)
        )
        alternate_config["Blur_Before_Canny"] = True  # Apply more blurring before edge detection

    elif error_type == "NoSubphotosExtracted":
        # Increase contrast adjustments and adaptive thresholding
        alternate_config["Content_Threshold_Ratio"] *= 0.8  # Lower the threshold for detecting content
        alternate_config["Hough_Threshold"] = max(50, default_config["Hough_Threshold"] - 30)  # More relaxed line detection

    elif error_type == "SkewCorrectionFailure":
        # Increase the tolerance for detecting horizontal lines
        alternate_config["Hough_Threshold"] = max(50, default_config["Hough_Threshold"] - 30)
        alternate_config["Crop_Margin_Factor"] += 2  # Increase margin factor for skew correction

    print(f"Applying alternate config for {error_type}: {alternate_config}")
    return alternate_config

def monitor_ingest_folder(ingest_folder, photo_queue, processing_config, stop_event):
    """
    Monitors an ingest folder for new image files and enqueues them for processing.

    Args:
        ingest_folder (str): Path to the folder to monitor.
        config (dict): Configuration for image processing.
        photo_queue (Queue): Queue for storing Combined_Photo objects.
    """
    supported_extensions = ('.tiff', '.tif', '.png', '.jpg', '.jpeg', '.bmp', '.heic', '.webp')

    def process_new_file(image_path):
        print(f"New file detected: {image_path}")
        # Small settling delay to avoid reading while the file is still being written
        time.sleep(0.5)
        split_and_enqueue_photos(image_path, processing_config, photo_queue)

    class IngestFolderHandler(FileSystemEventHandler):
        """Handles file creation events in the monitored folder."""
        def on_created(self, event):
            if not event.is_directory:
                ext = os.path.splitext(str(event.src_path))[1].lower()
                if ext in supported_extensions:
                    process_new_file(event.src_path)

    # Set up folder monitoring
    observer = Observer()
    event_handler = IngestFolderHandler()
    observer.schedule(event_handler, ingest_folder, recursive=False)
    observer.start()
    print(f"Monitoring folder: {ingest_folder}")

    try:
        while not stop_event.is_set():  # Keep monitoring unless stop_event is set
            threading.Event().wait(timeout=1)  # Allows graceful exit

    except KeyboardInterrupt:
        print("Stopping folder monitoring...")

    observer.stop()  # Stops the observer thread
    observer.join()  # Ensures the observer thread fully stops
    print("Folder monitoring thread has stopped.")
    return

def reprocess_combined_photo(gui, config):
    """
    Allows the user to modify processing settings and returns the updated config.

    Args:
        gui (ImageEditorGUI): The GUI instance.
        config (dict): The current processing configuration.

    Returns:
        dict: Updated configuration.
    """

    print("Prompting user for new processing configuration...")
    updated_config = gui.prompt_for_new_config(config)
    return updated_config if updated_config else config  # Keep the same config if no update

def handle_combined_photo(gui, combined_photo, processing_config, stop_event):
    """
    Handles previewing and processing of a combined photo in an event-driven way.
    """
    def update_gui():
        if stop_event.is_set():  # Stop if quitting
            return
        gui.confirmation_variable.set("")  # Clear previous input
        gui.preview_all_subphotos(combined_photo)  # ✅ Thread-safe update

    # ✅ Request new configuration in a thread-safe manner
    def request_new_config():
        if stop_event.is_set():  # Stop if quitting
            return
        new_config = gui.prompt_for_new_config(processing_config)
        gui.confirmation_variable.set("new_config_ready")  # ✅ Signal that the new config is ready
        # Stash for retrieval after wait_variable
        setattr(gui, "_pending_new_config", new_config)
        return new_config

    gui.root.after(0, update_gui)

    while not stop_event.is_set():
        try:
            gui.root.wait_variable(gui.confirmation_variable)
        except RuntimeError:
            # This handles the case where the main loop has already been terminated
            break

        user_choice = gui.confirmation_variable.get()

        if stop_event.is_set():
            break  # Stop processing if quitting

        if user_choice == "process_subphotos":
            print(f"✅ User confirmed processing subphotos for {combined_photo.base_name}.")
            
            # ✅ Block until all subphotos are processed
            while not gui.subphoto_processing_complete and not stop_event.is_set():
                gui.root.wait_variable(gui.confirmation_variable)  # Wait for subphoto completion
                
            if gui.subphoto_processing_complete:
                print(f"✅ All subphotos processed for {combined_photo.base_name}.")
            return  # Exit after processing completes

        elif user_choice == "reprocess":
            print(f"🔄 User requested reprocessing for {combined_photo.base_name}.")

            gui.root.after(0, request_new_config)  # ✅ Run in the main thread

            gui.root.wait_variable(gui.confirmation_variable)  # ✅ Block until "new_config_ready" is set

            print("✅ Reprocessing with updated configuration.")

            # ✅ Apply new configuration
            new_config = getattr(gui, "_pending_new_config", processing_config)
            result = split_and_crop(combined_photo.combined_image, new_config)
            if isinstance(result, tuple) and len(result) >= 1:
                reprocessed_subphotos = result[0]
            else:
                reprocessed_subphotos = []
            combined_photo.subphotos = reprocessed_subphotos
            combined_photo.num_subphotos = len(reprocessed_subphotos)
            combined_photo.current_index = 0  # Reset index

            # ✅ Restart processing with the new configuration
            handle_combined_photo(gui, combined_photo, new_config, stop_event)
            return  # ✅ Exit after restarting
        
        elif user_choice == "quit_app":
            print(f"🚪 User exited or stop event triggered. Stopping processing for {combined_photo.base_name}.")
            return  # Exit safely

    return

def process_photos_in_gui(gui, photo_queue, processing_config, stop_event):
    """
    Main processing loop that dequeues combined photos and processes them.

    Args:
        gui (ImageEditorGUI): The GUI instance for user interaction.
        photo_queue (Queue): The queue containing Combined_Photo objects.
        output_base_folder (str): Folder where processed subphotos are saved.
        config (dict): Configuration settings.
        stop_event (threading.Event): Event to signal shutdown.
    """

    while not stop_event.is_set():
        try:
            combined_photo = photo_queue.get(timeout=1)
            print(f"Dequeued combined photo: {combined_photo.base_name}")

            handle_combined_photo(gui, combined_photo, processing_config, stop_event)

        except queue.Empty:
            if stop_event.is_set():
                print("Stopping photo processing thread...")
                break
    print("Photo processing thread has stopped.")
    return

def save_subphotos(subphoto_saving_queue, output_base_folder, saving_config, stop_event):
    """
    Continuously processes subphotos from the queue and saves them in order.
    """
    while not stop_event.is_set():
        try:
            subphoto = subphoto_saving_queue.get(timeout=1)  # Blocks until an item is available
            print(f"🔄 Saving subphoto {subphoto['part_number']}...")

            # ✅ Call `save_and_inject_metadata()` in the background
            save_and_inject_metadata(
                photo=subphoto["photo"],
                output_base_folder=output_base_folder,
                base_name=subphoto["base_name"],
                part_number=subphoto["part_number"],
                exif_date=f"{subphoto['metadata']['year']}:{subphoto['metadata']['mmdd'][:2]}:{subphoto['metadata']['mmdd'][2:]} 00:00:00",
                description=subphoto["metadata"]["description"],
                year=subphoto["metadata"]["year"],
                saving_config=saving_config
            )

            print(f"✅ Successfully saved subphoto {subphoto['part_number']}.")

            subphoto_saving_queue.task_done()  # Mark as processed

        except queue.Empty:
            continue  # Keep looping until stop_event is set

    print("Subphoto saving thread has stopped.")
    return

def main():
    """
    Main entry point for the photo processing application.

    Initializes configuration, GUI, and background threads for folder monitoring and photo processing.
    """
    DebugMode = True

    processing_config = {
        "Debug_Mode": DebugMode,
        "CUDA_Enabled": True,              # Enable CUDA acceleration (if available)
        "Max_Scanned_Photos": 4,
        "Min_Crop_Margin": 10,              # Crop margin for 0° skew
        "Crop_Margin_Factor": 8,            # Scaling factor to achieve 50 pixels at 5° skew
        "Max_Crop_Margin": 100,             # Upper limit for extreme skew angles
        "Blur_Before_Canny": False,
        "Projection_Smoothing_Sigma": 5,    # Strength of noise reduction for horizontal/vertical projection (row/column sums)
        "Threshold_Std_Scale": 3.0,         # Identifies horizontal boundaries based on prominence
        "SP_Smoothing_Kernel_Ratio": 200,   # Single-pass smoothing kernel ratio
        "MP_Smoothing_Kernel_Ratio": 200,   # Multi-pass smoothing kernel ratio
        "Canny_Threshold_Scale": (0.66, 1.33),
        "Canny_Thresholds": (50, 150),
        "Content_Threshold_Ratio": 0.01,
        "Horizontal_Boundary_Threshold": 0.6,
        "Hough_Threshold": 150,
        "Skew_Angle_Threshold": 10,
        "Skew_ROI_Margin": 0.05
    }

    saving_config = {
        "Debug_Mode": DebugMode,
        "Save_As_HEIC": True,  # Save in HEIC format
        "HEIC_Quality": 100,
        "Save_As_JPEG": True,  # Save in JPEG format
        "JPEG_Quality": 100,
        "Save_As_PNG": False,  # Optionally enable PNG saving
        "Save_As_TIFF": False  # Optionally enable TIFF saving
    }

    gui_config = {
        "Debug_Mode": DebugMode,
        "Background_Color_1": "#0F0F0F",       # Set the background color of the window
        "Background_Color_2": "#181818",
        "Default_Window_Size": "1400x900+100+100",      # Set the initial window size and position it at 100,100
        "Display_Mode": "windowed_fullscreen"     # fullscreen, windowed_fullscreen, or None
    }

    application_root = os.path.dirname(os.path.abspath(__file__))
    output_base_folder = os.path.abspath(os.path.join(application_root, "Processed Photos"))
    ingest_folder = os.path.join(application_root, "Ingest")

    os.makedirs(output_base_folder, exist_ok=True)
    os.makedirs(ingest_folder, exist_ok=True)

    if DebugMode:
        debug_output_folder = os.path.join(application_root, "Debug Output")
        os.makedirs(debug_output_folder, exist_ok=True)
        processing_config["Debug_Output_Path"] = debug_output_folder

    subphoto_saving_queue = Queue()
    photo_queue = Queue()
    stop_event = threading.Event()

    subphoto_saving_thread = threading.Thread(
        target=save_subphotos,
        args=(subphoto_saving_queue, output_base_folder, saving_config, stop_event),
        daemon=True
    )
    subphoto_saving_thread.start()

    # Initialize the GUI
    gui = ImageEditorGUI(gui_config, subphoto_saving_queue, stop_event)

    # Start thread for monitoring the ingest folder
    # This thread is also responsible for automatically splitting, cropping, and queueing subphotos
    # PRODUCER THREAD
    folder_monitoring_thread = threading.Thread(
        target=monitor_ingest_folder,
        args=(ingest_folder, photo_queue, processing_config, stop_event),
        daemon=True
    )
    folder_monitoring_thread.start()

    # Start thread for processing photos
    # CONSUMER THREAD
    process_thread = threading.Thread(
        target=process_photos_in_gui,
        args=(gui, photo_queue, processing_config, stop_event),
        daemon=True
    )
    process_thread.start()

    # Start the GUI event loop
    gui.root.mainloop()

    subphoto_saving_thread.join()
    process_thread.join()
    folder_monitoring_thread.join()

if __name__ == "__main__":
    main()