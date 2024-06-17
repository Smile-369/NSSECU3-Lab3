import os
import sys
import subprocess
import tempfile
import argparse
import pandas as pd
from regipy.plugins.utils import dump_hive_to_json, json
from regipy.registry import RegistryHive
import ctypes
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

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
    """Install required packages and libraries."""
    required_packages = ["regipy", "pandas", "tqdm"]
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

def parse_registry_hive(hive_path, output_dir):
    try:
        hive_object = RegistryHive(hive_path)
        with tempfile.NamedTemporaryFile(delete=True, suffix=".json") as temp_json:
            json_output_path = temp_json.name
        dump_hive_to_json(hive_object, json_output_path, name_key_entry=None, verbose=True)

        with open(json_output_path, 'r') as json_file:
            json_dframe = [json.loads(line.strip()) for line in json_file if line.strip()]

        df = pd.DataFrame(json_dframe)
        csv_file_path = os.path.join(output_dir, os.path.basename(hive_path) + ".csv")

        # Parse the CSV file with pandas and display the content
        df.dropna(how="all", inplace=True)
        df.rename(columns=lambda x: x.capitalize(), inplace=True)
        df.drop(['Actual_path'], axis=1, inplace=True)
        df.reset_index(drop=True, inplace=True)

        df = move_column_to_first(df, 'Path')
        df = move_column_to_first(df, 'Timestamp')
        df = df.sort_values(by='Timestamp', ascending=False)
        df['Timestamp'] = df['Timestamp'].str.replace('T', ' T-').str.split('.').str[0]

        #Push df to csv filepath
        df.to_csv(csv_file_path, index=False)

        print(f"Successfully parsed {hive_path} and saved to {csv_file_path}")
    except Exception as e:
        print(f"Failed to parse registry hive {os.path.basename(hive_path)}: {e}")

def move_column_to_first(df, column_name):
    if column_name in df.columns:
        columns = [column_name] + [col for col in df.columns if col != column_name]
        df = df[columns]
    return df

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
    parser.add_argument('-v', '--save-hives', action='store_true', help="Flag to save the SAM, SYSTEM, SOFTWARE, and SECURITY hives.")
    parser.add_argument('-m','--sam-file', type=str, help="Path to the SAM file.")
    parser.add_argument('-y','--system-file', type=str, help="Path to the SYSTEM file.")
    parser.add_argument('-w','--software-file', type=str, help="Path to the SOFTWARE file.")
    parser.add_argument('-c','--security-file', type=str, help="Path to the SECURITY file.")
    parser.add_argument('-d','--default-file', type=str, help="Path to the DEFAULT file.")
    parser.add_argument('-o','--output-dir', type=str, help="Directory where the CSV files will be saved.")
    args = parser.parse_args()

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

    def process_hive(hive_path):
        parse_registry_hive(hive_path, output_dir)

    hives_to_process = []

    if args.save_hives:
        with tempfile.TemporaryDirectory() as temp_dir:
            if args.sam_file:
                sam_file = args.sam_file
            else:
                sam_file = os.path.join(temp_dir, "sam")
                save_registry_hive(r"HKLM\SAM", sam_file)
            hives_to_process.append(sam_file)

            if args.system_file:
                system_file = args.system_file
            else:
                system_file = os.path.join(temp_dir, "system")
                save_registry_hive(r"HKLM\SYSTEM", system_file)
            hives_to_process.append(system_file)

            if args.software_file:
                software_file = args.software_file
            else:
                software_file = os.path.join(temp_dir, "software")
                save_registry_hive(r"HKLM\SOFTWARE", software_file)
            hives_to_process.append(software_file)

            if args.security_file:
                security_file = args.security_file
            else:
                security_file = os.path.join(temp_dir, "security")
                save_registry_hive(r"HKLM\SECURITY", security_file)
            hives_to_process.append(security_file)

            if args.default_file:
                default_file = args.default_file
            else:
                default_file = os.path.join(temp_dir, "default")
                save_registry_hive(r"HKEY_USERS\.DEFAULT", default_file)
            hives_to_process.append(default_file)

            with ThreadPoolExecutor() as executor:
                list(tqdm(executor.map(process_hive, hives_to_process), total=len(hives_to_process), desc="Processing hives"))
    else:
        if args.sam_file:
            hives_to_process.append(args.sam_file)
        if args.system_file:
            hives_to_process.append(args.system_file)
        if args.software_file:
            hives_to_process.append(args.software_file)
        if args.security_file:
            hives_to_process.append(args.security_file)
        if args.default_file:
            hives_to_process.append(args.default_file)

        if not hives_to_process:
            print("No hive files provided to parse.")
            return

        with ThreadPoolExecutor() as executor:
            list(tqdm(executor.map(process_hive, hives_to_process), total=len(hives_to_process), desc="Processing hives"))

if __name__ == "__main__":
    main()
