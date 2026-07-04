# YT Downloader

![python](https://img.shields.io/badge/python-3.x-3776AB?style=flat-square)

A graphical YouTube video downloader application built with Python and yt-dlp, featuring a modern UI with download quality options and playlist support.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Features
- Download YouTube videos in MP4 (video) or MP3 (audio) formats
- Multiple quality presets for both formats:
  - MP4: Best quality, 1080p, 720p, 480p, 360p
  - MP3: 320kbps, 256kbps, 192kbps, 128kbps, 96kbps
- Playlist download support with progress tracking
- Customizable download directory (defaults to ~/Downloads/mp4 or ~/Downloads/mp3)
- Modern GUI with dark theme
- Real-time download progress indicators:
  - Current file progress
  - Playlist progress (when applicable)
  - Download speed and ETA

## Requirements
- Python 3.x
- Required packages (automatically installed via requirements.txt):
  - tkinter (usually included with Python)
  - yt-dlp
  - requests

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/yt-downloader-python.git
   cd yt-downloader-python
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Run the application with:
```bash
python youtube-download.py
```

The application will launch with a graphical interface where you can:
1. Paste a YouTube URL (video or playlist)
2. Select format (MP4/MP3)
3. Choose quality preset
4. Optionally change download directory
5. Click "TÉLÉCHARGER" to start download

## Project Structure
```
yt-downloader-python/
├── .gitignore
├── README.md
├── requirements.txt
└── youtube-download.py
```

- `youtube-download.py`: Main application file containing the GUI and download logic
- `requirements.txt`: Lists all Python dependencies

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

<!-- TODO: Add contribution guidelines if project grows -->