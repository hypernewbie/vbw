import csv
from pathlib import Path


def main() -> None:
    # This script aggregates profanity lists from various CSV and TXT files,
    # removes duplicates, and writes the unique entries to a single CSV file.

    base_dir = Path(__file__).resolve().parent
    target_csv = base_dir / "profanity_aggregate.csv"

    # Gather all source files from specified directories: CSV files from 'profanity_csv'
    # and TXT files from 'profanity-list-main/list'.

    source_files = sorted(
        path
        for path in base_dir.glob("profanity_csv/*.csv")
    )
    source_files.extend(
        sorted(
            path
            for path in base_dir.glob("profanity-list-main/list/*.txt")
        )
    )

    if not source_files:
        raise SystemExit("No source CSV or TXT files found to aggregate.")

    # Process each source file, reading its content and adding unique rows to a set.
    # CSV files are read using csv.reader, and TXT files are read line by line.

    unique_rows = set()
    for source_file in source_files:
        print(f"Processing {source_file} ...")
        if source_file.suffix == ".csv":
            with source_file.open("r", encoding="utf-8", newline="") as infile:
                reader = csv.reader(infile)
                for row in reader:
                    if row:
                        unique_rows.add(tuple(row))
        elif source_file.suffix == ".txt":
            with source_file.open("r", encoding="utf-8") as infile:
                for line in infile:
                    word = line.strip()
                    if word:
                        unique_rows.add((word,))

    # Write all collected unique rows to the target CSV file, sorted alphabetically.

    with target_csv.open("w", encoding="utf-8", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerows(sorted(list(unique_rows)))

    print(f"Wrote {len(unique_rows)} unique rows from {len(source_files)} CSV and TXT files to {target_csv.name}")


if __name__ == "__main__":
    main()

