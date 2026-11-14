# Google Drive Direct Link Generator

A Python script that generates direct download/streaming links from Google Drive URLs, with automatic handling of virus scan warnings. Supports both individual files and folders, creating M3U playlists for video folders.

## Features

- 🔗 **Direct Link Generation**: Converts Google Drive share links to direct download URLs
- 🛡️ **Virus Scan Bypass**: Automatically handles Google's virus scan warnings for large files
- 📁 **Folder Support**: Processes entire folders and generates M3U playlists for all video files
- 📂 **Nested Folder Support**: Recursively handles nested folder structures and creates appropriate directory layouts
- 🎵 **VLC Streaming**: Generated links work seamlessly with VLC Media Player
- 🔐 **Secure Authentication**: Uses OAuth 2.0 for Google Drive API access
- 📋 **M3U Playlists**: Creates organized playlist files for folder contents
- 📊 **Smart Organization**: Automatically sorts videos by filename and creates folders only when needed
- 🎬 **Recursive Processing**: Handles deeply nested folder hierarchies automatically

## Prerequisites

- Python 3.6 or higher
- Google Cloud Console account with Drive API enabled
- `credentials.json` file from Google Cloud Console

## Setup

### 1. Google Cloud Console Setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Drive API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API" and enable it
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the credentials as `credentials.json`

### 2. Installation

1. Clone or download this repository
2. Place your `credentials.json` file in the project root directory
3. Install required Python packages:

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests
```

## Usage

### Makefile Quick Commands

You can use `make` for quick command execution with positional file paths and URLs:

```bash
# Upload a file or folder directly
make upload ./file.txt
make upload /workspaces/dd-fe/README.md
make upload ./my_folder PARENT=<parent_folder_id>

# Stream / Generate direct link or M3U playlist
make stream <Google-Drive-URL-or-ID>
# or
make run <Google-Drive-URL-or-ID>

# Download a file or folder
make download <Google-Drive-URL-or-ID> [DIR=down_files]

# List Google Drive folders
make list-folders
```

### Basic Usage (Python Scripts)

```bash
python drive_stream_v2.py <Google Drive URL or ID>
```

### Examples

#### Individual File
```bash
python drive_stream_v2.py https://drive.google.com/file/d/1O_6sH8eew8YscxR4WzI7zxrQ2r25gXTi/view?usp=drive_link
```

#### Folder (Generates M3U Playlist)
```bash
python drive_stream_v2.py https://drive.google.com/drive/folders/1-7IK1sZ_vqphG6L8zrtDOpacUGckLQnC?usp=drive_link
```

#### Using File/Folder ID Directly
```bash
python drive_stream_v2.py 1O_6so3eUN8YsaZR4WzI7zxZQ2C25gXTi
```

### Output

- **For Files**: Displays file information and direct streaming link
- **For Folders**: Creates M3U playlist files in the `v_link/` directory containing all video files
- **For Nested Folders**: Creates a hierarchical folder structure with M3U files at each level

### Nested Folder Example

When processing a folder with nested structure:

```
Google Drive Folder (input)
├── Section 01 (folder with only videos)
│   ├── 001 Chapter 1.mp4
│   ├── 002 Chapter 2.mp4
│   └── 003 Chapter 3.mp4
├── Section 02 (folder with only videos)
│   ├── 001 Intro.mp4
│   └── 002 Main.mp4
```

Generated local structure:

```
v_link/
├── Google Drive Folder/
│   ├── Section 01.m3u (contains links to 3 videos)
│   └── Section 02.m3u (contains links to 2 videos)
```

**Note**: Videos are automatically sorted by filename within each M3U file for proper playback order.

## How It Works

1. **Authentication**: Uses OAuth 2.0 to authenticate with Google Drive API
2. **URL Parsing**: Extracts file or folder ID from Google Drive URLs
3. **File Processing**:
   - Retrieves file metadata (name, size, permissions)
   - Generates direct download link
   - Handles virus scan warnings automatically
4. **Folder Processing**:
   - Recursively lists all video files and nested folders
   - Separates videos from folders intelligently
   - Sorts videos by filename for proper playback order
   - Generates direct links for each video
   - Creates M3U playlist with all video links
5. **Smart Directory Structure**:
   - If a folder has **only videos**: Creates M3U file directly in parent folder
   - If a folder has **nested folders**: Creates a subfolder and processes recursively
   - Automatically organizes deeply nested structures

## M3U Playlist Format

Generated playlists follow the standard M3U format:

```
#EXTM3U
#EXTINF:-1,Video Name.mp4
https://drive.usercontent.google.com/download?id=...&export=download&confirm=...&uuid=...
#EXTINF:-1,Another Video.mkv
https://drive.usercontent.google.com/download?id=...&export=download&confirm=...&uuid=...
```

## VLC Streaming

1. Copy the generated direct link
2. Open VLC Media Player
3. Go to Media → Open Network Stream
4. Paste the link and click Play

For M3U playlists, simply open the `.m3u` file directly in VLC.

## Troubleshooting

### Common Issues

- **"credentials.json not found"**: Ensure you've downloaded and placed the credentials file in the project root
- **Authentication errors**: Delete `token.pickle` and re-run to re-authenticate
- **Permission denied**: Ensure the Google Drive files/folders are publicly shared
- **No video files in folder**: The script only processes video MIME types (video/*)

### Virus Scan Handling

The script automatically detects and bypasses Google's virus scan warnings by:
1. Attempting the standard download URL
2. Checking for virus scan warning page
3. Extracting confirmation parameters
4. Generating the bypass URL

## File Structure

```
drive-direct-link_m3u/
├── drive_stream_v2.py     # Main script
├── credentials.json       # Google API credentials (not included)
├── token.pickle          # OAuth token (generated)
├── v_link/               # Generated M3U playlists and folders
│   ├── Parent Folder/
│   │   ├── Section 1.m3u
│   │   ├── Section 2.m3u
│   │   └── Section 3.m3u
│   └── Single Videos.m3u
└── README.md             # This file
```

## Security Notes

- Never share your `credentials.json` or `token.pickle` files
- The script only requires read-only access to Google Drive
- All generated links are direct download URLs that bypass some Google restrictions

## License

This project is open source. Feel free to modify and distribute.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure all prerequisites are met
3. Verify Google Drive sharing permissions
4. Check that the URLs are valid and accessible
