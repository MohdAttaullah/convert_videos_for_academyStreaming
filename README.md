# Video Conversion Utility

A production-ready Python utility to recursively find, convert, and safely manage `.mp4` video files using `ffmpeg`. It is optimized for course videos (720p scaling, libx264, AAC audio, and web-optimized).

## Features
- **Recursive Scanning**: Finds all `.mp4` files in subfolders.
- **Dry-run Mode**: Preview what will happen without making any changes.
- **Smart Renaming**: Extracts numbers from filenames and cleans up special characters automatically.
- **Safe Deletion**: Original files are only deleted after strict safety checks (e.g., verifying the output file size and extension).
- **Parallel Processing**: Uses multi-threading to convert multiple files simultaneously.
- **Comprehensive Logging**: Detailed terminal and file logging (`conversion_log.txt`).

## Requirements

- Python 3.7+
- `ffmpeg` must be installed and available in your system's PATH. 
  - To confirm if `ffmpeg` is installed, run this command in PowerShell:
    ```powershell
    Get-Command ffmpeg
    ```

## Setup

It is recommended to use a virtual environment. Run these commands from your root folder (`DE_By_Summit`):

1. **Create a virtual environment:**
   ```powershell
   python -m venv .venv
   ```

2. **Activate the virtual environment (Windows PowerShell):**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   *(Note: This project relies on standard libraries, but the requirements.txt is provided for convention)*
   ```powershell
   pip install -r requirements.txt
   ```

## Usage

### 1. Dry Run Mode
By default, the script is configured to safely preview the process.
1. Open `convert_all_videos_recursive.py`.
2. Ensure `DRY_RUN = True` at the top of the file.
3. Run the script:
   ```powershell
   python convert_all_videos_recursive.py
   ```
4. Review the terminal output and the `conversion_log.txt` to verify the new filenames and what will happen.

### 2. Actual Conversion
1. Open `convert_all_videos_recursive.py`.
2. Change the configuration:
   ```python
   DRY_RUN = False
   ```
3. Run the script:
   ```powershell
   python convert_all_videos_recursive.py
   ```
4. The script will show a warning: `WARNING: DRY_RUN is disabled.` and ask you to type `Y` to confirm before proceeding.

### 3. Change Parallel Processing Speed
By default, `MAX_PARALLEL_JOBS = 2` to safely convert files without overloading your CPU.
To process more files concurrently, change this variable at the top of the script:
```python
MAX_PARALLEL_JOBS = 3  # or whatever your system can handle
```

## How Deletion Safety Works
When `DRY_RUN = False`, the script will ONLY delete the original file if:
- ffmpeg returns a success code (`0`).
- The new 720p output file exists and is strictly greater than 0 bytes.
- The output file has the `_720.mp4` suffix.
- The output file is located in the exact same directory as the input file.
- The output file path is genuinely different from the original file path.
