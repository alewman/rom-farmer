import subprocess
import glob
from pathlib import Path
import sys

def import_all_metadata():
    # Find all gamelist.xml files
    gamelist_files = sorted(glob.glob("/data/emu/roms/*/gamelist.xml"))
    
    total = len(gamelist_files)
    print(f"Found {total} gamelist.xml files to import.")
    
    success_count = 0
    fail_count = 0
    
    for i, gamelist_path in enumerate(gamelist_files, 1):
        path = Path(gamelist_path)
        system = path.parent.name
        
        print(f"\n[{i}/{total}] Importing metadata for system: {system}")
        print(f"Path: {path}")
        
        try:
            # Run the import command
            cmd = [
                sys.executable, 
                "-m", 
                "romfarmer", 
                "metadata", 
                "import-arrm", 
                str(path)
            ]
            
            # Run and capture output to avoid cluttering unless error
            result = subprocess.run(
                cmd, 
                cwd="/data/emu/rom-farmer-python",
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"✅ Success: {system}")
                success_count += 1
            else:
                print(f"❌ Failed: {system}")
                print("Error output:")
                print(result.stderr)
                fail_count += 1
                
        except Exception as e:
            print(f"❌ Error executing import for {system}: {e}")
            fail_count += 1

    print("\n" + "="*50)
    print(f"Import Complete")
    print(f"Successful: {success_count}")
    print(f"Failed:     {fail_count}")
    print("="*50)

if __name__ == "__main__":
    import_all_metadata()
