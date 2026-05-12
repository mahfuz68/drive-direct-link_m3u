#!/usr/bin/env python3
"""
Google Drive File Downloader
Downloads files and folders from Google Drive using file/folder ID or shareable link.
"""

import io
import os
import sys
import argparse
import pickle
import re
from pathlib import Path
from typing import Optional, Tuple

DOWNLOAD_DIR = "down_files"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.pickle"
FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
GOOGLE_EXPORTS = {
    "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
    ),
    "application/vnd.google-apps.presentation": ("application/pdf", ".pdf"),
    "application/vnd.google-apps.drawing": ("image/png", ".png"),
}


def format_size(num_bytes: Optional[int]) -> str:
    """Return a human-readable byte count."""
    if not num_bytes:
        return "unknown size"

    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024

    return f"{num_bytes} B"


def print_progress_bar(
    downloaded: int,
    total: Optional[int],
    *,
    prefix: str = "  Progress",
    width: int = 32,
) -> None:
    """Render a single-line terminal progress bar."""
    if total and total > 0:
        ratio = min(max(downloaded / total, 0), 1)
        filled = int(width * ratio)
        bar = "#" * filled + "-" * (width - filled)
        percent = ratio * 100
        print(
            f"\r{prefix}: [{bar}] {percent:6.2f}% "
            f"({format_size(downloaded)} / {format_size(total)})",
            end="",
            flush=True,
        )
        return

    print(
        f"\r{prefix}: {format_size(downloaded)} downloaded",
        end="",
        flush=True,
    )


def sanitize_name(name: str) -> str:
    """Make a Drive item name safe for local filesystems."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip() or "untitled"


def extract_drive_id(value: str, default_kind: str = "file") -> Tuple[str, str]:
    """Return (kind, id) for a Google Drive file/folder URL or raw ID."""
    folder_match = re.search(r"/folders/([a-zA-Z0-9_-]+)", value)
    if folder_match:
        return "folder", folder_match.group(1)

    file_match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", value)
    if file_match:
        return "file", file_match.group(1)

    id_match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", value)
    if id_match:
        return default_kind, id_match.group(1)

    return default_kind, value


def authenticate_google_drive():
    """Authenticate with Google Drive API."""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        print("Error: Google Drive API packages are not installed.")
        print(
            "Install them with: "
            "pip install google-auth google-auth-oauthlib google-api-python-client"
        )
        return None

    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"Error: {CREDENTIALS_FILE} not found.")
                print("Download it from Google Cloud Console and put it here.")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def download_drive_file(
    service,
    file_id: str,
    output_dir: str,
    show_progress: bool = True,
) -> bool:
    """Download a single Drive file into output_dir."""
    try:
        from googleapiclient.http import MediaIoBaseDownload
    except ImportError:
        print("Error: google-api-python-client is not installed.")
        return False

    metadata = service.files().get(
        fileId=file_id,
        fields="id,name,mimeType,size",
        supportsAllDrives=True,
    ).execute()
    name = sanitize_name(metadata.get("name", file_id))
    mime_type = metadata.get("mimeType", "")
    total_size = int(metadata.get("size", 0) or 0)
    os.makedirs(output_dir, exist_ok=True)

    if mime_type in GOOGLE_EXPORTS:
        export_mime_type, extension = GOOGLE_EXPORTS[mime_type]
        if not Path(name).suffix:
            name = f"{name}{extension}"
        request = service.files().export_media(
            fileId=file_id,
            mimeType=export_mime_type,
        )
    else:
        request = service.files().get_media(
            fileId=file_id,
            supportsAllDrives=True,
        )

    output_path = os.path.join(output_dir, name)
    print(f"Downloading: {output_path}")

    with io.FileIO(output_path, "wb") as file_handle:
        downloader = MediaIoBaseDownload(file_handle, request)
        done = False
        downloaded = 0
        chunk_total = total_size
        while not done:
            status, done = downloader.next_chunk()
            if status and show_progress:
                downloaded = getattr(status, "resumable_progress", 0)
                chunk_total = getattr(status, "total_size", None) or total_size
                if not downloaded and chunk_total:
                    downloaded = int(status.progress() * chunk_total)
                print_progress_bar(downloaded, chunk_total)

    if show_progress:
        print_progress_bar(downloaded, chunk_total)
        print()
    print(f"✓ Downloaded: {output_path}")
    return True


def download_drive_folder(
    service,
    folder_id: str,
    output_dir: str,
    show_progress: bool = True,
) -> bool:
    """Recursively download a Google Drive folder into output_dir."""
    folder = service.files().get(
        fileId=folder_id,
        fields="id,name",
        supportsAllDrives=True,
    ).execute()
    folder_name = sanitize_name(folder.get("name", folder_id))
    local_folder = os.path.join(output_dir, folder_name)
    os.makedirs(local_folder, exist_ok=True)
    print(f"Folder: {folder_name}")

    success = True
    page_token = None
    while True:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken,files(id,name,mimeType)",
            pageSize=1000,
            pageToken=page_token,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
        ).execute()

        for item in results.get("files", []):
            if item.get("mimeType") == FOLDER_MIME_TYPE:
                success = download_drive_folder(
                    service,
                    item["id"],
                    local_folder,
                    show_progress,
                ) and success
            else:
                success = download_drive_file(
                    service,
                    item["id"],
                    local_folder,
                    show_progress,
                ) and success

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    return success


def download_file_gdown(
    file_id_or_url: str,
    output_path: Optional[str] = None,
    quiet: bool = False
) -> bool:
    """
    Download file from Google Drive using gdown.
    
    Args:
        file_id_or_url: Google Drive file ID or shareable link
        output_path: Output file path (optional)
        quiet: Suppress progress output
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import gdown
    except ImportError:
        print("Error: gdown is not installed.")
        print("Install it with: pip install gdown")
        return False
    
    try:
        file_id = file_id_or_url
        
        # Extract file ID from full URL if needed
        if file_id_or_url.startswith("http"):
            if "/d/" in file_id_or_url:
                try:
                    file_id = file_id_or_url.split("/d/")[1].split("/")[0]
                except IndexError:
                    print("✗ Could not extract file ID from URL")
                    return False
            url = f"https://drive.google.com/uc?id={file_id}"
        else:
            url = f"https://drive.google.com/uc?id={file_id}"
        
        print(f"Downloading from: {url}")
        
        # Download file
        output = gdown.download(
            url,
            output=output_path,
            quiet=quiet
        )
        
        if output:
            print(f"✓ Downloaded successfully to: {output}")
            return True
        else:
            print("✗ Download failed")
            return False
            
    except Exception as e:
        print(f"✗ Error downloading file: {e}")
        return False


def download_file_requests(
    file_id: str,
    output_path: Optional[str] = None,
    quiet: bool = False,
) -> bool:
    """
    Download file from Google Drive using requests (fallback method).
    
    Args:
        file_id: Google Drive file ID
        output_path: Output file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import requests
    except ImportError:
        print("Error: requests is not installed.")
        print("Install it with: pip install requests")
        return False
    
    try:
        url = f"https://drive.google.com/uc?id={file_id}&export=download"
        
        session = requests.Session()
        response = session.get(url, stream=True)
        
        # Handle confirmation for large files
        for key, value in response.cookies.items():
            if key.startswith("download_warning"):
                url = f"{url}&confirm={value}"
                response = session.get(url, stream=True)
                break
        
        if response.status_code != 200:
            print(f"✗ Error: Server returned status {response.status_code}")
            return False
        
        # Get filename from headers if not provided
        if not output_path:
            content_disposition = response.headers.get("content-disposition", "")
            if "filename=" in content_disposition:
                output_path = content_disposition.split("filename=")[1].strip('"')
            else:
                output_path = file_id
        
        # Download file
        total_size = int(response.headers.get("content-length", 0))
        downloaded_size = 0

        if not quiet:
            print(f"Downloading: {output_path} ({format_size(total_size)})")
        
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if not quiet:
                        print_progress_bar(downloaded_size, total_size)
        
        if not quiet:
            print_progress_bar(downloaded_size, total_size)
            print()
        print(f"✓ Downloaded successfully to: {output_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error downloading file: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download files or folders from Google Drive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download using file ID
  python google_drive_downloader.py 1-file-id-here
  
  # Download using shareable link
  python google_drive_downloader.py "https://drive.google.com/file/d/1-file-id-here/view?usp=sharing"

  # Download a folder using shareable link
  python google_drive_downloader.py "https://drive.google.com/drive/folders/1-folder-id-here?usp=sharing"

  # Download a folder using raw folder ID
  python google_drive_downloader.py 1-folder-id-here --type folder
  
  # Download and save with custom filename
  python google_drive_downloader.py 1-file-id-here -o myfile.zip
  
  # Use fallback method (requests instead of gdown)
  python google_drive_downloader.py 1-file-id-here --method requests
        """
    )
    
    parser.add_argument(
        "file_id",
        help="Google Drive file/folder ID or shareable link"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (optional)",
        default=None
    )
    parser.add_argument(
        "-d", "--dir", "--directory",
        help="Download directory (default: current directory)",
        default=None
    )
    parser.add_argument(
        "-m", "--method",
        choices=["gdown", "requests"],
        default="gdown",
        help="File download method. Folders always use the Google Drive API (default: gdown)"
    )
    parser.add_argument(
        "-t", "--type",
        choices=["auto", "file", "folder"],
        default="auto",
        help="Input type. Use --type folder when passing a raw folder ID (default: auto)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output"
    )
    
    args = parser.parse_args()
    
    default_kind = "folder" if args.type == "folder" else "file"
    item_kind, item_id = extract_drive_id(args.file_id, default_kind=default_kind)
    if args.type != "auto":
        item_kind = args.type

    download_dir = args.dir or DOWNLOAD_DIR

    if not os.path.exists(download_dir):
        os.makedirs(download_dir, exist_ok=True)

    if item_kind == "folder":
        service = authenticate_google_drive()
        if not service:
            return 1
        success = download_drive_folder(service, item_id, download_dir, not args.quiet)
        return 0 if success else 1
    
    output_path = args.output
    if output_path and not os.path.isabs(output_path):
        output_path = os.path.join(download_dir, output_path)
    elif not output_path:
        output_path = download_dir
    
    # Download using selected method
    if args.method == "gdown":
        success = download_file_gdown(item_id, output_path, args.quiet)
    else:
        success = download_file_requests(item_id, output_path, args.quiet)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
