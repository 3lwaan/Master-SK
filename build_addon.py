import os
import zipfile

def build_zip():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(script_dir, "MasterSK.zip")
    
    exclude_dirs = {"__pycache__", ".git", ".vscode"}
    exclude_files = {"MasterSK.zip", "build_addon.bat", "build_addon.py", ".DS_Store", "blender_manifest.toml"}
    exclude_exts = {".pyc", ".pyo", ".blend1"}
    
    print(f"Packaging MasterSK.zip (Legacy Addon format)...")
    
    if os.path.exists(zip_path):
        os.remove(zip_path)
        
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(script_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file in exclude_files:
                    continue
                _, ext = os.path.splitext(file)
                if ext in exclude_exts:
                    continue
                    
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, script_dir)
                archive_name = os.path.join("MasterSK", rel_path)
                
                zipf.write(full_path, archive_name)
                print(f"  + {archive_name}")
                
    print(f"\nSUCCESS: Created '{zip_path}' (Legacy Addon format)")

if __name__ == "__main__":
    build_zip()
