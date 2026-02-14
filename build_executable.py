# build_executable.py
# Builds a standalone .exe file from the trading GUI
# Usage: python build_executable.py

import os
import sys
import shutil
from pathlib import Path

def build_exe():
    """Build executable using PyInstaller"""
    
    print("="*60)
    print("ML TRADING SYSTEM - EXECUTABLE BUILDER")
    print("="*60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("\n❌ PyInstaller not found!")
        print("Installing PyInstaller...")
        os.system(f"{sys.executable} -m pip install PyInstaller -q")
    
    # Paths
    project_root = Path(__file__).parent.parent
    services_dir = project_root / "services"
    dist_dir = project_root / "dist"
    
    print(f"\n📁 Project root: {project_root}")
    print(f"📁 Services dir: {services_dir}")
    print(f"📁 Output dir: {dist_dir}")
    
    # Create build command
    # Important flags:
    # --onefile: Single executable file
    # --windowed: No console window (GUI only)
    # --add-data: Include data files
    # --hidden-import: Include modules that PyInstaller can't detect
    
    output_name = "MLTradingSystem"
    
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                           # Single executable
        "--windowed",                          # GUI (no console)
        "--name", output_name,                 # Output name
        "--distpath", str(dist_dir),          # Output directory
        "--specpath", str(project_root / "build"),
        "--buildpath", str(project_root / "build"),
        
        # Add services as data
        f"--add-data={services_dir}{os.pathsep}services",
        
        # Hidden imports for PyInstaller to find
        "--hidden-import=sklearn",
        "--hidden-import=sklearn.ensemble",
        "--hidden-import=sklearn.preprocessing",
        "--hidden-import=joblib",
        "--hidden-import=pandas",
        "--hidden-import=numpy",
        "--hidden-import=yfinance",
        "--hidden-import=alpaca.trading",
        "--hidden-import=PyQt5.QtChart",
        
        # Icon (optional - create if you have one)
        # f"--icon={project_root / 'icon.ico'}",
        
        str(services_dir / "trading_gui.py"),
    ]
    
    print("\n🔨 Building executable...")
    print("Command:", " ".join(pyinstaller_cmd))
    print()
    
    # Run PyInstaller
    result = os.system(" ".join(pyinstaller_cmd))
    
    if result == 0:
        print("\n✅ BUILD SUCCESSFUL!")
        exe_path = dist_dir / f"{output_name}.exe"
        print(f"\n📦 Executable created: {exe_path}")
        print(f"📊 File size: {exe_path.stat().st_size / (1024*1024):.1f} MB")
        
        # Create run script
        run_script = project_root / "RUN.bat"
        with open(run_script, 'w') as f:
            f.write(f"@echo off\n")
            f.write(f"cd /d \"%~dp0\"\n")
            f.write(f"dist\\{output_name}.exe\n")
            f.write(f"pause\n")
        
        print(f"✅ Run script created: {run_script}")
        
        return True
    else:
        print("\n❌ BUILD FAILED!")
        print("Check the output above for errors.")
        return False


def clean_build():
    """Clean up build artifacts"""
    project_root = Path(__file__).parent.parent
    
    print("\n🧹 Cleaning up build artifacts...")
    
    dirs_to_remove = [
        project_root / "build",
        project_root / "__pycache__",
        project_root / "services" / "__pycache__",
    ]
    
    for dir_path in dirs_to_remove:
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  Removed: {dir_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build ML Trading System executable")
    parser.add_argument("--clean", action="store_true", help="Clean build artifacts after building")
    parser.add_argument("--clean-only", action="store_true", help="Only clean, don't build")
    
    args = parser.parse_args()
    
    if args.clean_only:
        clean_build()
    else:
        success = build_exe()
        
        if args.clean and success:
            clean_build()
        
        if success:
            print("\n" + "="*60)
            print("🚀 Ready to distribute!")
            print("="*60)
            print("\nNext steps:")
            print("1. Commit to GitHub: git add . && git commit -m 'Build executable'")
            print("2. Push to GitHub: git push origin main")
            print("3. Create release on GitHub with dist/MLTradingSystem.exe")
            print("4. Easy download & run on any Windows machine!")
