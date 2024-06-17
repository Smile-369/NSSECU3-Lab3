import pandas as pd
import argparse

def readCSV(file):
    """reading CSV file for Parsing"""
    try:
        df = pd.read_csv(file)
        df.dropna(how="all", inplace=True)
        df.rename(columns=lambda x: x.capitalize(), inplace=True)
        df.drop(['Actual_path'], axis=1, inplace=True)
        df.reset_index(drop=True, inplace=True)

        df = move_column_to_first(df, 'Path')
        df = move_column_to_first(df, 'Timestamp')
        df = df.sort_values(by='Timestamp', ascending=False)
        df['Timestamp'] = df['Timestamp'].str.replace('T', ' T-').str.split('.').str[0]

        pd.set_option('display.max_columns', None)
        print(df)
    except PermissionError as e:
        print(f"Permission Denied: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

def move_column_to_first(df, column_name):
    if column_name in df.columns:
        columns = [column_name] + [col for col in df.columns if col != column_name]
        df = df[columns]
    return df

def main():
    parser = argparse.ArgumentParser(description="parse test data")
    parser.add_argument('file', help='run')
    args = parser.parse_args()

    readCSV(args.file)

if __name__ == "__main__":
    main()
