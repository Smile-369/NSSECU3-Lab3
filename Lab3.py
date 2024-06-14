import os
import sys
import subprocess
import tempfile
import argparse
import csv
import pandas as pd
from regipy.registry import RegistryHive
import ctypes

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Relaunch the script with administrative privileges."""
    script = os.path.abspath(sys.argv[0])
    params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
    try:
        subprocess.run(["runas", "/user:Administrator", f'python {script} {params}'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to elevate to admin: {e}")
        sys.exit(1)

def install_packages():
    required_packages = ["regipy", "pandas"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def save_registry_hive(hive, filename):
    try:
        subprocess.run(["reg", "save", hive, filename], check=True)
        print(f"Successfully saved {hive} to {filename}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to save {hive}: {e}")

def parse_registry_hive(file_path, output_dir=None):
    try:
        registry_hive = RegistryHive(file_path)
        if output_dir is None:
            output_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(output_dir, os.path.basename(file_path) + ".csv")
        
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=';', escapechar='\\', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(["Subkey", "Values"])
            
            for subkey in registry_hive.recurse_subkeys():
                values = []
                for value in subkey.values:
                    values.append(f"{value.name}: {value.value}")
                csv_writer.writerow([subkey.path, "; ".join(values)])
        
        print(f"Successfully parsed {file_path} and saved to {csv_file_path}")
        
        # Parse the CSV file with pandas and display the content
        df = pd.read_csv(csv_file_path, delimiter=';', escapechar='\\')
        print(f"Contents of {csv_file_path}:")
        print(df)
        
    except Exception as e:
        print(f"Failed to parse registry hive {file_path}: {e}")

def main():
    # Install required packages
    install_packages()

    # Elevate privileges if not already running as administrator
    if not is_admin():
        print("Not running as admin, attempting to relaunch with admin privileges...")
        run_as_admin()
        return

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Save registry hives or use provided files.")
    parser.add_argument('--save-hives', action='store_true', help="Flag to save the SAM, SYSTEM, SOFTWARE, and SECURITY hives.")
    parser.add_argument('--sam-file', type=str, help="Path to the SAM file.")
    parser.add_argument('--system-file', type=str, help="Path to the SYSTEM file.")
    parser.add_argument('--software-file', type=str, help="Path to the SOFTWARE file.")
    parser.add_argument('--security-file', type=str, help="Path to the SECURITY file.")
    parser.add_argument('--output-dir', type=str, help="Directory where the CSV files will be saved.")
    args = parser.parse_args()

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = None

    if args.save_hives:
        with tempfile.TemporaryDirectory() as temp_dir:
            sam_file = os.path.join(temp_dir, "sam")
            system_file = os.path.join(temp_dir, "system")
            software_file = os.path.join(temp_dir, "software")
            security_file = os.path.join(temp_dir, "security")
            
            save_registry_hive(r"HKLM\SAM", sam_file)
            save_registry_hive(r"HKLM\SYSTEM", system_file)
            save_registry_hive(r"HKLM\SOFTWARE", software_file)
            save_registry_hive(r"HKLM\SECURITY", security_file)
            
            parse_registry_hive(sam_file, output_dir)
            parse_registry_hive(system_file, output_dir)
            parse_registry_hive(software_file, output_dir)
            parse_registry_hive(security_file, output_dir)
    else:
        if not args.sam_file or not args.system_file or not args.software_file or not args.security_file:
            print("All --sam-file, --system-file, --software-file, and --security-file arguments must be provided if not using --save-hives.")
            return

        sam_file = args.sam_file
        system_file = args.system_file
        software_file = args.software_file
        security_file = args.security_file
        print(f"Using provided SAM file: {sam_file}")
        print(f"Using provided SYSTEM file: {system_file}")
        print(f"Using provided SOFTWARE file: {software_file}")
        print(f"Using provided SECURITY file: {security_file}")
        
        parse_registry_hive(sam_file, output_dir)
        parse_registry_hive(system_file, output_dir)
        parse_registry_hive(software_file, output_dir)
        parse_registry_hive(security_file, output_dir)

if __name__ == "__main__":
    main()
