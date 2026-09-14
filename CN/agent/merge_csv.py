import csv
import os


INPUT_FOLDER = "CN/data/raw"
OUTPUT_FILE = "CN/data/processed/sentinelnet_dataset.csv"


def merge_csv_files():

    csv_files = [
        "PC01.csv",
        "PC02.csv",
        "PC03.csv",
        "PC04.csv"
    ]

    all_rows = []

    for filename in csv_files:

        filepath = os.path.join(INPUT_FOLDER, filename)

        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found.")
            continue

        with open(filepath, "r", newline="") as file:

            reader = csv.DictReader(file)

            for row in reader:
                all_rows.append(row)

    if not all_rows:
        print("No data found.")
        return

    fieldnames = all_rows[0].keys()

    with open(OUTPUT_FILE, "w", newline="") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(all_rows)

    print("===================================")
    print("SentinelNet Dataset Merge")
    print("===================================")
    print("Files merged:", len(csv_files))
    print("Total sessions:", len(all_rows))
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    merge_csv_files()