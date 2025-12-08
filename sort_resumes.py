import os
import shutil
import re
import time
from datetime import date, datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

def get_todays_date():

    today = datetime.now()
    month = today.strftime("%b").lower()
    day = today.day
    year = today.year
    return f"{month}-{day}-{year}"

def clean_filename(file_name):
    file_name, extension = os.path.splitext(file_name)

    clean_name = re.sub(r'\s*\(\d+\)\s*$', '', file_name)
    return f"{clean_name}{extension}"

def get_latest_folder_date(resume_directory):
    """Get the date string from the most recent resume folder"""
    if not resume_directory.exists():
        return None
    
    latest_date = None
    latest_time = 0
    
    for item in resume_directory.iterdir():
        if item.is_dir() and "resume" in item.name.lower():
            # Remove "(Latest)" tag if present for parsing
            folder_name = item.name.replace(" (Latest)", "")
            # Try to extract date from folder name (format: month-day-year-resume-number)
            parts = folder_name.split("-resume-")
            if len(parts) >= 1:
                date_part = parts[0]
                # Check if this looks like a date (month-day-year)
                if len(date_part.split("-")) == 3:
                    folder_time = item.stat().st_mtime
                    if folder_time > latest_time:
                        latest_time = folder_time
                        latest_date = date_part
    
    return latest_date

def archive_old_folders(base_dir, current_date_string):
    """Move all existing folders to Resume History if date has changed"""
    resume_directory = Path(base_dir) / "Resumes"
    if not resume_directory.exists():
        return
    
    latest_date = get_latest_folder_date(resume_directory)
    
    # If no folders exist or date matches today, does not archive
    if latest_date is None or latest_date == current_date_string:
        return
    
    # Date has changed, move all folders to Resume History
    history_dir = resume_directory / "Resume History"
    history_dir.mkdir(exist_ok=True)
    
    folders_to_move = []
    for item in resume_directory.iterdir():
        if item.is_dir() and item.name != "Resume History":
            folders_to_move.append(item)
    
    if folders_to_move:
        print(f"Date changed from {latest_date} to {current_date_string}. Archiving {len(folders_to_move)} folder(s) to Resume History...")
        for folder in folders_to_move:
            try:
                target = history_dir / folder.name
                shutil.move(str(folder), str(target))
                print(f"  Moved: {folder.name} -> Resume History/")
            except Exception as e:
                print(f"  Error moving {folder.name}: {e}")

def remove_latest_tag(resume_directory):
    """Remove (Latest) tag from any folder that has it"""
    if not resume_directory.exists():
        return
    
    for item in resume_directory.iterdir():
        if item.is_dir() and " (Latest)" in item.name:
            new_name = item.name.replace(" (Latest)", "")
            try:
                item.rename(resume_directory / new_name)
            except Exception as e:
                print(f"Error removing (Latest) tag from {item.name}: {e}")

def add_latest_tag(folder_path):
    """Add (Latest) tag to the specified folder"""
    if " (Latest)" in folder_path.name:
        return  # Already has the tag
    
    new_name = folder_path.name + " (Latest)"
    try:
        folder_path.rename(folder_path.parent / new_name)
    except Exception as e:
        print(f"Error adding (Latest) tag to {folder_path.name}: {e}")

def get_next_resume_iteration(base_dir, date_string):
    resume_directory  = Path(base_dir) / "Resumes"
    if not resume_directory.exists():
        return 1

    pattern = f"{date_string}-resume"
    max_iteration = 0

    for item in resume_directory.iterdir():
        if item.is_dir():
            # Remove "(Latest)" tag for parsing
            folder_name = item.name.replace(" (Latest)", "")
            if folder_name.startswith(pattern):
                try:
                    iteration_string = folder_name.split("resume-")[-1]
                    current_iteration = int(iteration_string)
                    max_iteration = max(max_iteration, current_iteration)
                except ValueError:
                    continue

    return max_iteration + 1

def resume_was_created_today(file_path):
    today = datetime.now().date()
    try:
        stat_info = file_path.stat()
        if hasattr(stat_info, 'st_birthtime'):
            file_time = datetime.fromtimestamp(stat_info.st_birthtime)
        else:
            file_time = datetime.fromtimestamp(stat_info.st_mtime)
        file_date = file_time.date()
        return file_date == today
    except (OSError, AttributeError):
        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        file_date = file_time.date()
        return file_date == today

def process_single_resume(resume_file_path, base_dir):
    """Process a single resume file"""
    resume_file = Path(resume_file_path)
    
    if not resume_file.exists():
        return
    
    if not resume_file.is_file():
        return
    
    if 'resume' not in resume_file.name.lower():
        return
    
    if not resume_was_created_today(resume_file):
        print(f"Skipping {resume_file.name} - not created today")
        return
    
    date_string = get_todays_date()
    resume_dir = Path(base_dir) / "Resumes"
    resume_dir.mkdir(exist_ok=True)
    
    archive_old_folders(base_dir, date_string)
    
    remove_latest_tag(resume_dir)
    
    current_iteration = get_next_resume_iteration(base_dir, date_string)
    target_dir = resume_dir / f"{date_string}-resume-{current_iteration}"
    target_dir.mkdir(exist_ok=True)
    
    cleaned_filename = clean_filename(resume_file.name)
    target_file = target_dir / cleaned_filename
    
    # delay to ensure file is fully written
    time.sleep(0.5)
    
    try:
        shutil.move(str(resume_file), str(target_file))
        add_latest_tag(target_dir)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Moved: {resume_file.name} -> {target_file}")
    except Exception as e:
        print(f"Error moving {resume_file.name}: {e}")

def process_resumes(source_dir, base_dir=None):
    """Process all resumes in source directory (batch mode)"""
    if base_dir is None:
        base_dir = os.getcwd()

    source_path = Path(source_dir)
    if not source_path.exists():
        print(f"Error: source dir '{source_dir} does not exist'")
        return
    
    # Filter resumes that were created today
    resume_files = []
    for file in source_path.iterdir():
        if file.is_file() and 'resume' in file.name.lower():
            if resume_was_created_today(file):
                resume_files.append(file)
            else:
                print(f"Skipping {file.name} - not created today")

    if not resume_files:
        print(f"No resumes created today were found in '{source_dir}'")
        return
    
    date_string = get_todays_date()
    resume_dir = Path(base_dir) / "Resumes"
    resume_dir.mkdir(exist_ok=True)
    
    archive_old_folders(base_dir, date_string)
    
    remove_latest_tag(resume_dir)

    current_iteration = get_next_resume_iteration(base_dir, date_string)
    latest_folder = None

    for resume_file in resume_files:
        target_dir = resume_dir / f"{date_string}-resume-{current_iteration}"
        target_dir.mkdir(exist_ok=True)

        cleaned_filename = clean_filename(resume_file.name)
        target_file = target_dir / cleaned_filename

        shutil.move(str(resume_file), str(target_file))
        print(f"Moved: {resume_file.name} -> {target_file}")
        
        latest_folder = target_dir
        current_iteration += 1
    
    # Add (Latest) tag to the most recent folder created
    if latest_folder:
        add_latest_tag(latest_folder)

class ResumeHandler(FileSystemEventHandler):
    """Handler for file system events"""
    def __init__(self, base_dir):
        self.base_dir = base_dir
    
    def on_created(self, event):
        if not event.is_directory:
            # Wait a moment for file to be fully written
            time.sleep(1)
            process_single_resume(event.src_path, self.base_dir)

if __name__ == "__main__":
    import sys

    load_dotenv()
    
    # Default to Downloads folder unless a unique paht is set in .env by the user
    default_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    SOURCE_DIRECTORY = os.getenv('SOURCE_DIRECTORY', default_downloads)
    BASE_DIRECTORY = os.getenv('BASE_DIRECTORY', default_downloads)
    
    # Run in watch mode (default) or batch mode (single use)
    if len(sys.argv) > 1 and sys.argv[1] == "--batch":
        # Batch mode: process all existing resumes once
        print("Running resume sorting in batch mode...")
        process_resumes(SOURCE_DIRECTORY, BASE_DIRECTORY)
    else:
        # Watch mode: continously monitor folder for new files
        print(f"Watching '{SOURCE_DIRECTORY}' for new resumes...")
        print("Press Ctrl+C to stop")
        
        event_handler = ResumeHandler(BASE_DIRECTORY)
        observer = Observer()
        observer.schedule(event_handler, SOURCE_DIRECTORY, recursive=False)
        observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping resume watcher...")
            observer.stop()
        observer.join()

