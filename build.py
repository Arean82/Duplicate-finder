#!/usr/bin/env python3
"""
Build script for JSON Duplicate Finder
Works on Windows, macOS, and Linux
Run: python build.py
"""

import os
import sys
import subprocess
import shutil
import platform
from pathlib import Path

def clean_build():
    """Clean previous build files"""
    folders = ['build', 'dist', '__pycache__']
    for folder in folders:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"✅ Removed {folder}/")
    
    # Remove spec file
    for spec in Path('.').glob('*.spec'):
        spec.unlink()
        print(f"✅ Removed {spec.name}")
    
    # Clean application subfolder pycache
    app_pycache = Path("application/__pycache__")
    if app_pycache.exists():
        shutil.rmtree(app_pycache)
        print(f"✅ Removed application/__pycache__/")
    
    print("✅ Clean complete!\n")

def create_resources_folder():
    """Create resources folder structure if not exists"""
    resources_dir = Path("resources")
    badges_dir = resources_dir / "badges"
    
    resources_dir.mkdir(exist_ok=True)
    badges_dir.mkdir(exist_ok=True)
    
    print("✅ Resources folder structure ready")

def get_separator():
    """Get OS-specific path separator for PyInstaller"""
    if platform.system() == 'Windows':
        return ';'
    else:
        return ':'

def build_executable():
    """Build executable for current platform"""
    system = platform.system()
    print(f"\n🔨 Building for: {system}")
    print(f"   Python: {sys.version}")
    print(f"   Platform: {platform.platform()}\n")
    
    # Check if required files exist (in application folder)
    app_dir = Path("application")
    required_files = [
        app_dir / "backend.py",
        app_dir / "frontend.py", 
        app_dir / "file_viewer.py",
    ]
    
    missing = [f.name for f in required_files if not f.exists()]
    
    if missing:
        print("❌ Missing required files in 'application' folder:")
        for f in missing:
            print(f"   - application/{f}")
        return False
    
    # Check root files
    root_files = ['aboutus.md', 'README.md', 'LICENSE', 'run.py']
    missing_root = [f for f in root_files if not Path(f).exists()]
    
    if missing_root:
        print("❌ Missing required files in root folder:")
        for f in missing_root:
            print(f"   - {f}")
        return False
    
    # Create resources folder if needed
    create_resources_folder()
    
    # Get OS-specific separator
    sep = get_separator()
    
    # Build command - with application folder as source
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name', 'JSON_Duplicate_Finder',
        '--add-data', f'aboutus.md{sep}.',
        '--add-data', f'README.md{sep}.',
        '--add-data', f'LICENSE{sep}.',
        '--add-data', f'resources{sep}resources',
        '--add-data', f'application{sep}application',  # Include entire application folder
        '--hidden-import', 'markdown',
        '--hidden-import', 'PySide6.QtCore',
        '--hidden-import', 'PySide6.QtWidgets',
        '--hidden-import', 'PySide6.QtGui',
        '--hidden-import', 'markdown.extensions.extra',
        '--hidden-import', 'markdown.extensions.fenced_code',
        '--hidden-import', 'markdown.extensions.codehilite',
        '--hidden-import', 'concurrent.futures',
        '--collect-all', 'markdown',
        '--paths', 'application',  # Add application folder to Python path
        'run.py'
    ]
    
    # Run PyInstaller
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Build complete for {system}!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {e}")
        return False
    except FileNotFoundError:
        print("\n❌ PyInstaller not found! Install it with: pip install pyinstaller")
        return False

def main():
    print("="*60)
    print("JSON Duplicate Finder - Build Script")
    print(f"OS Detected: {platform.system()}")
    print("="*60)
    
    # Show current folder structure
    print("\n📁 Current folder structure:")
    print("   - run.py (entry point)")
    print("   - application/")
    print("       ├── backend.py")
    print("       ├── frontend.py")
    print("       └── file_viewer.py")
    print("   - resources/")
    print("       ├── badges/")
    print("       └── badge_cache/")
    print("   - aboutus.md, README.md, LICENSE")
    
    # Check PyInstaller
    try:
        result = subprocess.run(['pyinstaller', '--version'], capture_output=True, text=True, check=True)
        print(f"\n✅ PyInstaller version: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n❌ PyInstaller is not installed!")
        print("   Install it with: pip install pyinstaller\n")
        return
    
    # Ask about cleaning
    response = input("\nClean previous builds? (y/n): ").strip().lower()
    if response == 'y':
        clean_build()
    
    # Build
    if build_executable():
        print("\n" + "="*60)
        print("✅ SUCCESS! Executable created in 'dist' folder:")
        if platform.system() == 'Windows':
            print("   dist/JSON_Duplicate_Finder.exe")
        else:
            print("   dist/JSON_Duplicate_Finder")
        print("="*60)
        
        # Show file size
        exe_name = "JSON_Duplicate_Finder.exe" if platform.system() == 'Windows' else "JSON_Duplicate_Finder"
        exe_path = Path("dist") / exe_name
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n📦 File size: {size_mb:.2f} MB")
    else:
        print("\n❌ Build failed. Check errors above.")

if __name__ == "__main__":
    main()