import os
import sys
import PyInstaller.__main__

def create_version_file():
    version_info = """VSVersionInfo(
      ffi=FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
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
            [StringStruct('CompanyName', 'LV Nexus Architecture'),
            StringStruct('FileDescription', 'LV Nexus - Next-Gen Windows Performance Architecture'),
            StringStruct('FileVersion', '2.1.0.0'),
            StringStruct('InternalName', 'LV_Nexus'),
            StringStruct('LegalCopyright', '© 2026 LV Nexus Architecture'),
            StringStruct('OriginalFilename', 'LV_Nexus.exe'),
            StringStruct('ProductName', 'LV Nexus'),
            StringStruct('ProductVersion', '1.0.0')])
          ]), 
        VarFileInfo([VarStruct('Translation', [1033, 1200])])
      ]
    )"""
    
    with open("version_info.txt", "w", encoding="utf-8") as f:
        f.write(version_info)

def build_exe():
    print("[*] Generating Version Info...")
    create_version_file()
    
    base_dir = os.path.abspath(os.path.dirname(__file__))
    main_script = os.path.join(base_dir, "main.py")
    
    # Dashboard path to include
    html_folder = os.path.join(base_dir, "gui")
    
    # Check if user has an icon.ico, if not skip icon
    icon_path = os.path.join(base_dir, "icon.ico")
    has_icon = os.path.exists(icon_path)
    
    print("[*] Starting PyInstaller Build Process...")
    
    pyinstaller_args = [
        main_script,
        '--name=LV_Nexus',
        '--onefile',                   # Single executable
        '--windowed',                  # Hidden console
        '--uac-admin',                 # Admin prompt on launch
        f'--add-data={html_folder};gui', # Include HTML/assets
        '--version-file=version_info.txt', # Version metadata
        '--clean',
        '--noconfirm'
    ]
    
    if has_icon:
        print(f"[*] Found custom icon: {icon_path}")
        pyinstaller_args.append(f'--icon={icon_path}')
    else:
        print("[!] No 'icon.ico' found in directory. Building without custom icon.")
        
    PyInstaller.__main__.run(pyinstaller_args)
    
    print("\n[+] BUILD COMPLETE! Your executable is located in the 'dist' folder.")

if __name__ == "__main__":
    build_exe()
