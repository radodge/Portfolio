> Version 1 of the application is in active development in a private repository to safeguard intellectual property. This folder contains a legacy v0 prototype suitable for demos.

## Legacy v0 Demo

Run a quick, self-contained demo of the legacy photo digitization GUI.

### Prerequisites

- Python 3.10+ (Windows recommended)
- Optional: ExifTool on PATH for metadata injection (https://exiftool.org/)

### Setup

From this folder in PowerShell:

```powershell
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -U pip
pip install -r requirements.txt
```

### Launch

```powershell
python run_legacy_demo.py
```

What happens:
- App creates these folders if missing: `Ingest`, `Processed Photos`, `Debug Output`.
- A background watcher monitors `Ingest` for new images.

### Try it

Drop an image into `Ingest` (supported: .tif/.tiff/.png/.jpg/.jpeg/.bmp/.heic/.webp). The app will:
1) Auto-split the composite into subphotos.
2) Let you preview and confirm.
3) Save subphotos into `Processed Photos` (HEIC and JPEG by default) and inject metadata if ExifTool is available.

Tip: In Debug mode, use the menu Debug → Simulate Ingest File to trigger processing with existing files in `Ingest`.

### Notes

- CUDA is disabled by default. Enable in `legacy_main_processing.py` if your OpenCV build supports CUDA.
- HEIC read/write handled via `pillow-heif`.
- Metadata injection is skipped gracefully when ExifTool is not installed.