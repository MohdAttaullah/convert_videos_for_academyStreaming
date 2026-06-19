import sys
import logging
import re
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

DRY_RUN = False
MAX_PARALLEL_JOBS = 2
LOG_FILE_NAME = "conversion_log.txt"

def setup_logger(root_dir: Path):
    logger = logging.getLogger("VideoConverter")
    logger.setLevel(logging.INFO)
    
    # Create terminal handler
    c_handler = logging.StreamHandler(sys.stdout)
    # Create file handler
    f_handler = logging.FileHandler(root_dir / LOG_FILE_NAME, encoding='utf-8')
    
    log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)
    
    # Avoid adding handlers multiple times if instantiated again
    if not logger.handlers:
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)
    return logger

def check_ffmpeg_available(logger):
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        logger.error("ffmpeg is not available in PATH. Please install ffmpeg and add it to your system PATH.")
        return False

def find_mp4_files(root_dir: Path):
    # Recursively find all mp4 files
    return [p for p in root_dir.rglob("*.mp4") if p.is_file()]

def clean_filename(name: str):
    # Remove unnecessary special characters
    name = re.sub(r'[^\w\s-]', '', name)
    # Replace multiple spaces with one underscore
    name = re.sub(r'\s+', '_', name)
    # Replace multiple underscores with one underscore
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores and hyphens
    name = name.strip('_-')
    return name

def extract_number_and_clean_title(base_name: str):
    # Try trailing number first: e.g. "-7", "_7", " 7"
    trailing_match = re.search(r'[-_\s]+(\d+)\s*$', base_name)
    if trailing_match:
        num = trailing_match.group(1).zfill(2)
        clean_base = base_name[:trailing_match.start()]
        return num, clean_filename(clean_base)
    
    # Try prefix number next: e.g. "1-Live Session"
    prefix_match = re.match(r'^\s*(\d+)[-_\s]+', base_name)
    if prefix_match:
        num = prefix_match.group(1).zfill(2)
        clean_base = base_name[prefix_match.end():]
        return num, clean_filename(clean_base)

    # Fallback to the first number found anywhere
    any_match = re.search(r'(\d+)', base_name)
    if any_match:
        num = any_match.group(1).zfill(2)
        clean_base = base_name[:any_match.start()] + base_name[any_match.end():]
        return num, clean_filename(clean_base)
    
    # No number found
    return "00", clean_filename(base_name)

def build_output_path(input_path: Path):
    num, clean_title = extract_number_and_clean_title(input_path.stem)
    new_name = f"{num}_{clean_title}_720.mp4"
    return input_path.parent / new_name

def should_skip_file(input_path: Path, output_path: Path, logger):
    if input_path.stem.endswith("_720"):
        logger.info(f"Skipping already converted file: {input_path.name}")
        return True, "Filename ends with _720"
    
    if output_path.exists():
        logger.info(f"Skipping: Output file already exists: {output_path.name}")
        return True, "Output file already exists"
        
    return False, ""

def convert_video(input_path: Path, output_path: Path, logger):
    logger.info(f"Processing: {input_path.name}")
    logger.info(f"Output: {output_path.name}")
    
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
    
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        return True
        
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return True
        else:
            logger.error(f"FFmpeg failed for {input_path.name}. Return code: {result.returncode}")
            logger.error(f"FFmpeg stderr: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Exception during conversion of {input_path.name}: {e}")
        return False

def delete_original_safely(input_path: Path, output_path: Path, logger):
    if DRY_RUN:
        logger.info(f"[DRY RUN] Would safely delete original file: {input_path.name}")
        return False
        
    try:
        # Safety conditions check
        if not output_path.exists():
            logger.warning(f"Safety check failed: Output file does not exist for {input_path.name}")
            return False
            
        if output_path.stat().st_size == 0:
            logger.warning(f"Safety check failed: Output file size is 0 for {input_path.name}")
            return False
            
        if input_path.resolve() == output_path.resolve():
            logger.warning(f"Safety check failed: Output path is same as input path for {input_path.name}")
            return False
            
        if input_path.parent.resolve() != output_path.parent.resolve():
            logger.warning(f"Safety check failed: Output is not in the same folder as input for {input_path.name}")
            return False
            
        if not output_path.name.endswith("_720.mp4"):
            logger.warning(f"Safety check failed: Output file does not end with _720.mp4 for {input_path.name}")
            return False
            
        # All checks passed, safe to delete
        logger.info(f"Deleting original file safely: {input_path.name}")
        input_path.unlink()
        return True
    except Exception as e:
        logger.error(f"Exception during safe delete of {input_path.name}: {e}")
        return False

def main():
    root_dir = Path.cwd()
    logger = setup_logger(root_dir)
    
    start_time = datetime.now()
    logger.info("--- Starting Video Conversion Job ---")
    logger.info(f"Start time: {start_time}")
    logger.info(f"Root folder path: {root_dir}")
    logger.info(f"Dry run status: {DRY_RUN}")
    logger.info(f"Max parallel jobs: {MAX_PARALLEL_JOBS}")
    
    if not check_ffmpeg_available(logger):
        sys.exit(1)
        
    if not DRY_RUN:
        print("\nWARNING: DRY_RUN is disabled.")
        print("Original files will be deleted after successful conversion.")
        confirm = input("Type Y to continue: ")
        if confirm.strip().upper() != "Y":
            logger.info("User cancelled execution. Exiting.")
            sys.exit(0)
            
    all_mp4_files = find_mp4_files(root_dir)
    logger.info(f"Total MP4 files found: {len(all_mp4_files)}")
    
    if not all_mp4_files:
        logger.info("No MP4 files found. Exiting.")
        sys.exit(0)
        
    planned_files = []
    skipped_count = 0
    
    # Pre-process to identify skip vs. planned files
    for f in all_mp4_files:
        out_path = build_output_path(f)
        skip, reason = should_skip_file(f, out_path, logger)
        if skip:
            skipped_count += 1
        else:
            planned_files.append((f, out_path))
            
    logger.info(f"Files planned for conversion: {len(planned_files)}")
    
    success_count = 0
    failed_count = 0
    deleted_count = 0
    kept_count = 0
    
    if planned_files:
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_JOBS) as executor:
            future_to_path = {
                executor.submit(convert_video, input_path, output_path, logger): (input_path, output_path)
                for input_path, output_path in planned_files
            }
            
            for future in as_completed(future_to_path):
                input_path, output_path = future_to_path[future]
                try:
                    success = future.result()
                    if success:
                        success_count += 1
                        if not DRY_RUN:
                            deleted = delete_original_safely(input_path, output_path, logger)
                            if deleted:
                                deleted_count += 1
                            else:
                                kept_count += 1
                        else:
                            # Simulated keep during dry run
                            kept_count += 1
                    else:
                        failed_count += 1
                        kept_count += 1
                except Exception as exc:
                    logger.error(f"{input_path.name} generated an exception: {exc}")
                    failed_count += 1
                    kept_count += 1
    
    end_time = datetime.now()
    
    logger.info("--- Conversion Job Finished ---")
    logger.info(f"End time: {end_time}")
    
    summary = f"""
========================================
Final summary:
Total MP4 files found:      {len(all_mp4_files)}
Already converted/skipped:  {skipped_count}
Planned for conversion:     {len(planned_files)}
Converted successfully:     {success_count}
Failed:                     {failed_count}
Original files deleted:     {deleted_count}
Original files kept:        {kept_count + skipped_count}
Log file location:          {root_dir / LOG_FILE_NAME}
========================================
"""
    print(summary)
    logger.info(summary)

if __name__ == "__main__":
    main()
