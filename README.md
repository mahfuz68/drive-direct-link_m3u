# Google Drive Direct Link Generator

A Python script that generates direct download/streaming links from Google Drive URLs, with automatic handling of virus scan warnings. Supports both individual files and folders, creating M3U playlists for video folders.

## Features

- 🔗 **Direct Link Generation**: Converts Google Drive share links to direct download URLs
- 🛡️ **Virus Scan Bypass**: Automatically handles Google's virus scan warnings for large files
- 📁 **Folder Support**: Processes entire folders and generates M3U playlists for all video files
- 🎵 **VLC Streaming**: Generated links work seamlessly with VLC Media Player
- 🔐 **Secure Authentication**: Uses OAuth 2.0 for Google Drive API access
- 📋 **M3U Playlists**: Creates organized playlist files for folder contents

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

### Basic Usage

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
- **For Folders**: Creates an M3U playlist file in the `v_link/` directory containing all video files

## How It Works

1. **Authentication**: Uses OAuth 2.0 to authenticate with Google Drive API
2. **URL Parsing**: Extracts file or folder ID from Google Drive URLs
3. **File Processing**:
   - Retrieves file metadata (name, size, permissions)
   - Generates direct download link
   - Handles virus scan warnings automatically
4. **Folder Processing**:
   - Lists all video files in the folder
   - Generates direct links for each video
   - Creates M3U playlist with all video links

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
agent-practice/
├── drive_stream_v2.py    # Main script
├── credentials.json      # Google API credentials (not included)
├── token.pickle         # OAuth token (generated)
├── v_link/              # Generated M3U playlists
│   └── Folder Name.m3u
└── README.md            # This file
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
