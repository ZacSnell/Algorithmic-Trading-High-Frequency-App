# auto_updater.py
# Checks GitHub for new releases and updates executable automatically

import os
import json
import requests
import subprocess
import sys
from pathlib import Path
from packaging import version
import shutil

class AutoUpdater:
    """Automatic update checker and installer"""
    
    def __init__(self, repo_owner="YourUsername", repo_name="Algorithmic-Trading-High-Frequency-App"):
        """
        Initialize updater
        
        Args:
            repo_owner: GitHub username/organization
            repo_name: Repository name
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_api = "https://api.github.com"
        self.current_version = "1.0.0"  # Update this with each release
        self.app_name = "MLTradingSystem"
    
    def get_latest_release(self):
        """Get latest release info from GitHub"""
        try:
            url = f"{self.github_api}/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                return response.json()
            else:
                print("❌ Failed to fetch release info")
                return None
        except Exception as e:
            print(f"❌ Error checking for updates: {e}")
            return None
    
    def has_update(self, latest_release):
        """Check if update is available"""
        if not latest_release:
            return False
        
        try:
            latest_version = latest_release['tag_name'].lstrip('v')
            current_ver = version.parse(self.current_version)
            latest_ver = version.parse(latest_version)
            
            return latest_ver > current_ver
        except:
            return False
    
    def download_update(self, latest_release, download_dir):
        """Download new executable from GitHub release"""
        try:
            # Find .exe file in assets
            assets = latest_release.get('assets', [])
            exe_asset = None
            
            for asset in assets:
                if self.app_name in asset['name'] and asset['name'].endswith('.exe'):
                    exe_asset = asset
                    break
            
            if not exe_asset:
                print("❌ No executable found in release")
                return False
            
            download_url = exe_asset['browser_download_url']
            filename = exe_asset['name']
            filepath = Path(download_dir) / filename
            
            print(f"⬇️  Downloading {filename}...")
            
            response = requests.get(download_url, stream=True, timeout=30)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"  Progress: {percent:.1f}%", end='\r')
            
            print(f"\n✅ Downloaded: {filepath}")
            return str(filepath)
        
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def install_update(self, new_exe_path, current_exe_path):
        """Install downloaded update"""
        try:
            # Create backup
            backup_path = Path(current_exe_path).parent / f"{self.app_name}_backup.exe"
            
            print(f"📦 Creating backup: {backup_path}")
            shutil.copy2(current_exe_path, backup_path)
            
            # Replace with new version
            print(f"📥 Installing update...")
            shutil.copy2(new_exe_path, current_exe_path)
            
            print(f"✅ Update installed successfully!")
            print(f"   Application will restart on next launch")
            
            return True
        
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False
    
    def check_and_update(self, show_dialog=True):
        """
        Check for updates and install if available
        
        Args:
            show_dialog: If True, show messages to user
        
        Returns:
            True if update installed, False otherwise
        """
        if show_dialog:
            print("\n🔍 Checking for updates...")
        
        # Get latest release
        latest = self.get_latest_release()
        
        if not latest:
            if show_dialog:
                print("⚠️  Could not check for updates")
            return False
        
        # Check version
        if not self.has_update(latest):
            if show_dialog:
                print("✅ You have the latest version")
            return False
        
        if show_dialog:
            print(f"\n🆙 Update available!")
            print(f"   Current: {self.current_version}")
            print(f"   Latest:  {latest['tag_name']}")
            print(f"   Release notes: {latest.get('body', 'No notes')}")
        
        # Download and install
        exe_path = self.download_update(latest, Path.home() / "Downloads")
        
        if exe_path:
            current_exe = Path(sys.executable)
            if self.install_update(exe_path, str(current_exe)):
                return True
        
        return False


def create_update_task_windows():
    """Create scheduled task to check for updates on Windows"""
    try:
        import ctypes
        
        # This would require admin privileges
        # For now, just show how to set it up manually
        print("""
        📋 To set up automatic update checking on Windows:
        
        1. Open Task Scheduler (taskschd.msc)
        2. Click "Create Basic Task"
        3. Name it: "ML Trading System Update Check"
        4. Set trigger: Daily at 06:00 AM
        5. Set action:
           Program: python.exe
           Arguments: "C:\\path\\to\\auto_updater.py --check-only"
        
        This will check for updates daily before market opens!
        """)
    except:
        pass


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-update ML Trading System")
    parser.add_argument("--check-only", action="store_true", help="Only check, don't install")
    parser.add_argument("--owner", default="YourUsername", help="GitHub repo owner")
    parser.add_argument("--repo", default="Algorithmic-Trading-High-Frequency-App", help="GitHub repo name")
    
    args = parser.parse_args()
    
    updater = AutoUpdater(args.owner, args.repo)
    
    if args.check_only:
        latest = updater.get_latest_release()
        if latest and updater.has_update(latest):
            print(f"✅ Update available: {latest['tag_name']}")
            print(f"   {latest.get('body', 'See release for details')}")
        else:
            print("✅ You have the latest version")
    else:
        updater.check_and_update()
