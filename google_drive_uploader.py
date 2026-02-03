#!/usr/bin/env python3
"""
Google Drive Folder Uploader
Upload folders to Google Drive from command line using Google Drive API.
"""

import os
import sys
import argparse
import pickle
import mimetypes
from pathlib import Path
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# OAuth 2.0 scopes
SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_FILE = os.path.expanduser('token.pickle')
CREDS_FILE = 'credentials.json'


def authenticate_oauth():
    """Authenticate using OAuth 2.0 (interactive)."""
    creds = None
    
    # Load saved credentials
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh or create new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        elif os.path.exists(CREDS_FILE):
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        else:
            print("Error: No credentials.json found")
            print("Download OAuth credentials from Google Cloud Console")
            return None
    
    # Save credentials for next run
    with open(TOKEN_FILE, 'wb') as token:
        pickle.dump(creds, token)
    
    return creds


def get_service(use_service_account: bool = False, 
                service_account_file: Optional[str] = None):
    """Get Google Drive API service."""
    try:
        if use_service_account and service_account_file:
            creds = Credentials.from_service_account_file(
                service_account_file, scopes=SCOPES)
        else:
            creds = authenticate_oauth()
            if not creds:
                return None
        
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"✗ Authentication error: {e}")
        return None


def create_folder(service, folder_name: str, 
                  parent_id: Optional[str] = None) -> Optional[str]:
    """Create a folder in Google Drive and return its ID."""
    try:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        return folder.get('id')
    except Exception as e:
        print(f"✗ Error creating folder: {e}")
        return None


def upload_file(service, file_path: str, 
                parent_id: Optional[str] = None,
                show_progress: bool = True) -> bool:
    """Upload a single file to Google Drive."""
    try:
        file_name = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        file_metadata = {'name': file_name}
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        file_size = os.path.getsize(file_path)
        
        if show_progress:
            print(f"  Uploading: {file_name} ({file_size / (1024*1024):.2f} MB)")
        
        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )
        
        request = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        )
        
        response = None
        while response is None:
            try:
                status, response = request.next_chunk()
                if status and show_progress:
                    percent = int(status.progress() * 100)
                    print(f"    Progress: {percent}%", end='\r')
            except Exception as e:
                print(f"\n    ✗ Error: {e}")
                return False
        
        if show_progress:
            print(f"    ✓ Uploaded successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error uploading file: {e}")
        return False


def upload_folder(service, local_path: str, 
                  parent_id: Optional[str] = None,
                  preserve_structure: bool = True) -> bool:
    """Upload a folder and its contents recursively."""
    try:
        if not os.path.isdir(local_path):
            print(f"✗ Error: {local_path} is not a directory")
            return False
        
        folder_name = os.path.basename(local_path.rstrip('/'))
        
        # Create folder in Drive
        drive_folder_id = create_folder(service, folder_name, parent_id)
        if not drive_folder_id:
            return False
        
        print(f"Created folder: {folder_name} (ID: {drive_folder_id})")
        
        # Upload files and subdirectories
        for root, dirs, files in os.walk(local_path):
            # Determine current folder ID
            if root == local_path:
                current_folder_id = drive_folder_id
            else:
                if preserve_structure:
                    relative_path = os.path.relpath(root, local_path)
                    subfolder_name = os.path.basename(root)
                    current_folder_id = create_folder(
                        service, subfolder_name, current_folder_id)
                    if not current_folder_id:
                        return False
                    print(f"  Created subfolder: {subfolder_name}")
                else:
                    current_folder_id = drive_folder_id
            
            # Upload files in current directory
            for file_name in files:
                file_path = os.path.join(root, file_name)
                if not upload_file(service, file_path, current_folder_id):
                    return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error uploading folder: {e}")
        return False


def list_drive_folders(service, max_results: int = 10) -> list:
    """List folders in Google Drive root."""
    try:
        query = "mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=max_results
        ).execute()
        
        return results.get('files', [])
    except Exception as e:
        print(f"✗ Error listing folders: {e}")
        return []


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Upload folders to Google Drive",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Upload a folder to Drive root
  python google_drive_uploader.py /path/to/folder
  
  # Upload with custom authentication
  python google_drive_uploader.py /path/to/folder --creds credentials.json
  
  # Upload to specific Drive folder (by ID)
  python google_drive_uploader.py /path/to/folder --parent-id FOLDER_ID
  
  # Use service account authentication
  python google_drive_uploader.py /path/to/folder --service-account sa.json
  
  # List existing folders in Drive
  python google_drive_uploader.py --list
  
  # Upload without preserving folder structure
  python google_drive_uploader.py /path/to/folder --no-structure
        """
    )
    
    parser.add_argument(
        "folder",
        nargs='?',
        help="Local folder path to upload"
    )
    parser.add_argument(
        "-p", "--parent-id",
        help="Google Drive folder ID to upload into (optional)",
        default=None
    )
    parser.add_argument(
        "-c", "--creds",
        help="Path to credentials.json file",
        default=CREDS_FILE
    )
    parser.add_argument(
        "-sa", "--service-account",
        help="Path to service account JSON file",
        default=None
    )
    parser.add_argument(
        "--no-structure",
        action="store_true",
        help="Don't preserve folder structure"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List folders in Drive root"
    )
    
    args = parser.parse_args()
    
    # Use provided credentials file or default
    creds_file = args.creds if args.creds else CREDS_FILE
    
    # Get service
    service = get_service(
        use_service_account=bool(args.service_account),
        service_account_file=args.service_account
    )
    
    if not service:
        return 1
    
    # List folders if requested
    if args.list:
        print("Folders in Google Drive:")
        folders = list_drive_folders(service)
        for folder in folders:
            print(f"  {folder['name']} (ID: {folder['id']})")
        return 0
    
    # Upload folder
    if not args.folder:
        parser.print_help()
        return 1
    
    print(f"Starting upload of: {args.folder}")
    success = upload_folder(
        service,
        args.folder,
        parent_id=args.parent_id,
        preserve_structure=not args.no_structure
    )
    
    if success:
        print("\n✓ Upload completed successfully!")
        return 0
    else:
        print("\n✗ Upload failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
