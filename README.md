# resume-sorting-tool
Makes applying easier by sorting downloaded resumes into structured folders.

# Example

<img width="1349" height="415" alt="image" src="https://github.com/user-attachments/assets/0157ed18-22dc-4b55-931d-9f0aa06d84c6" />

# Features

- **Automatic folder organization** - Sorts resumes into date-based folders (e.g., `dec-31-2025-resume-1`)
- **Real-time monitoring** - Watches the Downloads folder and automatically processes new resumes
- **Smart date detection** - Only processes resumes created today
- **Filename cleaning** - Removes duplicate markers like "(25)" from filenames
- **Auto-archiving** - Moves old resume folders to "Resume History" on the next day. This helps keep the directory clean.
- **Latest folder tagging** - Marks the most recent resume folder with "(Latest)" tag
- **Batch processing** - Process all existing resumes at once with `--batch` mode
- **Configurable paths** - Customize source and destination folders via `.env` file

## Clone & Run

1. Clone the repo: https://github.com/svastiks/resume-sortting-tool.git

2. Run: `pip install -r requirements.txt`

3. (Optional) Create and edit `.env` to change the default Downloads folder paths if needed. Only needed if you want to scan from and store into different paths.

4. `python3 sort_resumes.py` will run the tool with watcher and sort resumes automatically in the background.

OR

5. `python3 sort_resumes.py --batch` will process all existing resumes at once.
