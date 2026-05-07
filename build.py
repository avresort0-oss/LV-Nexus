"""
build.py — Advanced PyInstaller Build Automation for LV Nexus v2.1.0 Premium
====================================================================================

Automates the production-grade packaging of the application into a single
Windows executable. 

Features:
  - Automatic version metadata injection
  - UAC Manifest embedding for Admin rights
  - Hidden console window configuration
  - Resource bundling (HTML, Icons)
  - Automated cleaning of build artifacts
"""

import os
import sys
import shutil
import logging
from pathlib import Path
import PyInstaller.__main__

# --- Configuration ---
# Must match src/core_engine.py Config class
APP_NAME = "LV Nexus"
APP_FILENAME = "LV_Nexus"
VERSION = "2.1.0.0"
COMPANY = "LV Nexus Architecture"
DESCRIPTION = "Next-Gen Windows Performance Architecture"
COPYRIGHT = "© 2026 LV Nexus Architecture. All rights reserved."

# Configure logging for build script
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("Build")

def generate_version_info(output_path: Path):
    """Creates a Windows version info resource file."""
    v_tuple = tuple(int(x) for x in VERSION.split("."))
    
    content = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={v_tuple},
    prodvers={v_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', '{COMPANY}'),
        StringStruct('FileDescription', '{DESCRIPTION}'),
        StringStruct('FileVersion', '{VERSION}'),
        StringStruct('InternalName', '{APP_FILENAME}'),
        StringStruct('LegalCopyright', '{COPYRIGHT}'),
        StringStruct('OriginalFilename', '{APP_FILENAME}.exe'),
        StringStruct('ProductName', '{APP_NAME}'),
        StringStruct('ProductVersion', '{VERSION}')])
      ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    output_path.write_text(content, encoding="utf-8")
    logger.info(f"Version metadata generated at {output_path}")

def clean_workspace(base_dir: Path):
    """Removes previous build artifacts."""
    for folder in ['build', 'dist']:
        path = base_dir / folder
        if path.exists():
            shutil.rmtree(path)
            logger.info(f"Cleaned previous {folder} directory.")

def run_build():
    """Orchestrates the PyInstaller process."""
    print("\n" + "="*60)
    print(f"  🚀  BUILDING {APP_NAME} v{VERSION}  🚀  ")
    print("="*60 + "\n")
    
    base_dir = Path(__file__).parent.absolute()
    main_script = base_dir / "main.py"
    gui_folder = base_dir / "gui"
    icon_file = base_dir / "icon.ico"
    version_file = base_dir / "version_info.txt"

    # 1. Validation
    if not main_script.exists():
        logger.error(f"Main script not found: {main_script}")
        return
    if not gui_folder.exists():
        logger.error(f"GUI folder not found: {gui_folder}")
        return

    # 2. Cleanup
    clean_workspace(base_dir)
    
    # 3. Meta Generation
    generate_version_info(version_file)
    
    # 4. PyInstaller Command Construction
    # Note: On Windows, use ; as separator for --add-data
    separator = ";"
    
    args = [
        str(main_script),
        f"--name={APP_FILENAME}",
        "--onefile",
        "--windowed", # Hidden console
        "--uac-admin", # Force Admin rights on launch
        f"--add-data={gui_folder}{separator}gui",
        f"--version-file={str(version_file)}",
        "--clean",
        "--noconfirm",
        # Dependencies to ensure are included
        "--hidden-import=psutil",
        "--hidden-import=webview",
        "--hidden-import=GPUtil",
        "--hidden-import=wmi",
        "--hidden-import=winreg",
        "--hidden-import=clr" # Added for some hardware sensor fallbacks
    ]
    
    if icon_file.exists():
        args.append(f"--icon={str(icon_file)}")
        logger.info(f"Using custom icon: {icon_file}")
    else:
        logger.warning("No 'icon.ico' found. Using default executable icon.")

    logger.info("Initializing PyInstaller engine...")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n" + "="*60)
        print(f"  ✅ BUILD SUCCESSFUL: dist/{APP_FILENAME}.exe ")
        print("="*60 + "\n")
    except Exception as e:
        logger.error(f"Build Failed: {e}")

if __name__ == "__main__":
    run_build()
