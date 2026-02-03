#!/usr/bin/env python3
"""
Google Drive File Downloader
Downloads files from Google Drive using file ID or shareable link.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional


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
        # If it's a file ID, construct the URL
        if not file_id_or_url.startswith("http"):
            url = f"https://drive.google.com/uc?id={file_id_or_url}"
        else:
            url = file_id_or_url
        
        print(f"Downloading from: {url}")
        
        # Download file
        output = gdown.download(
            url,
            output=output_path,
            quiet=quiet,
            fuzzy=True
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
    output_path: Optional[str] = None
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
        
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded_size / total_size) * 100
                        print(f"\rDownloading: {percent:.1f}% ({downloaded_size}/{total_size} bytes)", end="")
        
        print(f"\n✓ Downloaded successfully to: {output_path}")
        return True
        
    except Exception as e:
        print(f"✗ Error downloading file: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download files from Google Drive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download using file ID
  python google_drive_downloader.py 1-file-id-here
  
  # Download using shareable link
  python google_drive_downloader.py "https://drive.google.com/file/d/1-file-id-here/view?usp=sharing"
  
  # Download and save with custom filename
  python google_drive_downloader.py 1-file-id-here -o myfile.zip
  
  # Use fallback method (requests instead of gdown)
  python google_drive_downloader.py 1-file-id-here --method requests
        """
    )
    
    parser.add_argument(
        "file_id",
        help="Google Drive file ID or shareable link"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (optional)",
        default=None
    )
    parser.add_argument(
        "-m", "--method",
        choices=["gdown", "requests"],
        default="gdown",
        help="Download method (default: gdown)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output"
    )
    
    args = parser.parse_args()
    
    # Create output directory if needed
    if args.output:
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    
    # Download using selected method
    if args.method == "gdown":
        success = download_file_gdown(args.file_id, args.output, args.quiet)
    else:
        # Extract file ID from URL if needed
        file_id = args.file_id
        if "drive.google.com" in file_id:
            try:
                file_id = file_id.split("/d/")[1].split("/")[0]
            except IndexError:
                print("✗ Could not extract file ID from URL")
                return 1
        success = download_file_requests(file_id, args.output)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
