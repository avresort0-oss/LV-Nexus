from PIL import Image
import os

png_path = r"C:\Users\Admin\.gemini\antigravity\brain\90b6a2f1-2e3e-4316-b855-31a6e156ed3c\lv_nexus_icon_1778158163141.png"
ico_path = r"C:\Users\Admin\Desktop\SUPPER SPPED PC\Antigravity_Idle\icon.ico"

print("Converting PNG to ICO...")
try:
    img = Image.open(png_path)
    # Resize to standard icon size and save
    img.save(ico_path, format="ICO", sizes=[(256, 256)])
    print("✅ Successfully created icon.ico in your project directory!")
    print("Now you can run 'python build.py' to build your executable with the new logo.")
except Exception as e:
    print(f"Error: {e}")
    print("If you don't have Pillow installed, run: pip install Pillow")
