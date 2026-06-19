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

## FFmpeg Conversion Parameters

The conversion command is carefully tuned for **course/academy streaming**: a good balance of visual quality, small file size, and smooth web playback. These values have been tested and validated for this use case.

> ⚠️ **Do not change these values unless you fully understand the trade-offs.** They are deliberately chosen to keep quality high while keeping files small and web-friendly. Changing them can break the quality/size balance, increase storage costs, or cause stuttering during streaming.

```python
cmd = [
    "ffmpeg",
    "-i", str(input_path),
    "-vf", "scale=-2:720",
    "-c:v", "libx264",
    "-preset", "slow",
    "-crf", "24",
    "-c:a", "aac",
    "-b:a", "96k",
    "-movflags", "+faststart",
    str(output_path)
]
```

| Parameter | Value | What it does | Why this value |
| --- | --- | --- | --- |
| `-i` | `input_path` | Specifies the **input** file to read. | Required — points ffmpeg at the source video. |
| `-vf` | `scale=-2:720` | Scales the **video height to 720p** and auto-computes the width to preserve the aspect ratio. The `-2` tells ffmpeg to pick a width that keeps the original ratio **and** is divisible by 2 (required by H.264). | 720p is the sweet spot for course content: text/slides stay sharp on most screens while files stay far smaller than 1080p/4K. Using `-2` (not a fixed width) avoids distortion and codec errors from odd dimensions. |
| `-c:v` | `libx264` | Sets the **video codec** to H.264 (x264 encoder). | H.264 is the most universally supported codec — it plays in every browser, phone, and player without extra plugins. Ideal for streaming reach. |
| `-preset` | `slow` | Controls **encoder speed vs. compression efficiency**. Slower presets compress better at the same quality. | `slow` gives noticeably smaller files at the same visual quality compared to `medium`/`fast`. Since conversion is a one-time batch job, spending more CPU time once to save storage and bandwidth forever is worth it. |
| `-crf` | `24` | **Constant Rate Factor** — the quality target. Lower = higher quality + bigger files; higher = lower quality + smaller files. Range is 0 (lossless) to 51 (worst). | `24` is tuned for screen-recorded / lecture content. It looks visually clean while keeping files small. Going below ~20 bloats size with no visible gain here; going above ~26 starts to blur text and slides. |
| `-c:a` | `aac` | Sets the **audio codec** to AAC. | AAC is the standard, widely-supported audio format for MP4 streaming — compatible everywhere. |
| `-b:a` | `96k` | Sets the **audio bitrate** to 96 kbps. | Course audio is mostly speech/voice, not music. 96 kbps is clear and intelligible for narration while using minimal space. Higher bitrates would waste storage with no audible benefit for talking. |
| `-movflags` | `+faststart` | Moves the MP4 **metadata (moov atom) to the front** of the file. | Essential for streaming: it lets the video **start playing before it fully downloads**. Without it, viewers must wait for the whole file to buffer. |
| (last arg) | `output_path` | The **output** file to write. | Required — the destination for the converted `_720.mp4` file. |

### Quick summary
- **Quality:** `crf 24` + `preset slow` → sharp text/slides at a small size.
- **Reach:** `libx264` + `aac` → plays everywhere.
- **Streaming:** `+faststart` → instant playback start.
- **Size:** `720p` + `96k audio` → optimized for storage and bandwidth.

**Bottom line: keep these values as-is** unless you have a specific, tested reason to change them.
