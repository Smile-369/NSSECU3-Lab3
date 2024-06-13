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

def parse_with_pecmd(file_path, output_dir):
    try:
        # Run PECmd command
        subprocess.run(["PECmd.exe", "-f", file_path, "--csv", output_dir], check=True)
        print(f"Successfully parsed {file_path} with PECmd")
    except subprocess.CalledProcessError as e:
        print(f"Failed to parse {file_path} with PECmd: {e}")

def parse_with_recmd(file_path, output_dir):
    try:
        # Run RECmd command
        subprocess.run(["./RECmd\RECmd.exe", "-f", file_path, "--csv", output_dir,"--sk URL"], check=True)
        print(f"Successfully parsed {file_path} with RECmd")
    except subprocess.CalledProcessError as e:
        print(f"Failed to parse {file_path} with RECmd: {e}")

def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Create a temporary directory for the registry hives
    with tempfile.TemporaryDirectory() as temp_dir:
        sam_file = os.path.join(temp_dir, "sam")
        system_file = os.path.join(temp_dir, "system")
        
        # Save the SAM and SYSTEM hives
        save_registry_hive(r"HKLM\SAM", sam_file)
        save_registry_hive(r"HKLM\SYSTEM", system_file)

        # Set the output directories for PECmd and RECmd
        output_dir_pecmd = os.path.join(script_dir, "pecmd_output")
        output_dir_recmd = os.path.join(script_dir, "recmd_output")
        
        # Create output directories if they don't exist
        os.makedirs(output_dir_pecmd, exist_ok=True)
        os.makedirs(output_dir_recmd, exist_ok=True)

        # Parse the saved hives with PECmd and RECmd
        # parse_with_pecmd(sam_file, output_dir_pecmd)
        parse_with_recmd(system_file, output_dir_recmd)

        # Print the output directories
        print(f"PECmd output directory: {output_dir_pecmd}")
        print(f"RECmd output directory: {output_dir_recmd}")

if __name__ == "__main__":
    main()
