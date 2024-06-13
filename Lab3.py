import os
import subprocess
import tempfile

def save_registry_hive(hive, filename):
    try:
        # Run the reg save command
        subprocess.run(["reg", "save", hive, filename], check=True)
        print(f"Successfully saved {hive} to {filename}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to save {hive}: {e}")

def main():
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        sam_file = os.path.join(temp_dir, "sam")
        system_file = os.path.join(temp_dir, "system")

        # Save the SAM and SYSTEM hives
        save_registry_hive(r"HKLM\SAM", sam_file)
        save_registry_hive(r"HKLM\SYSTEM", system_file)

        # Print the temporary directory location
        print(f"Registry hives saved in temporary directory: {temp_dir}")

if __name__ == "__main__":
    main()
