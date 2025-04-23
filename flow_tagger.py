import csv
import os
import sys
from collections import defaultdict

# Map protocol numbers to names
PROTOCOL_MAP = {
    "6": "tcp",
    "17": "udp",
    "1": "icmp"
}

def load_tag_lookup(lookup_file):
    tag_lookup = {}

    with open(lookup_file, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        expected_fields = {"dstport", "protocol", "tag"}
        sanitized_fieldnames = [h.strip().lower().replace('\ufeff', '') for h in reader.fieldnames]

        if sorted(sanitized_fieldnames) != sorted(expected_fields):
            raise ValueError(
                f"CSV header mismatch. Expected fields: {expected_fields}. Got: {reader.fieldnames}"
            )

        for row_num, raw_row in enumerate(reader, start=2):
            try:
                # Normalize each row key just like the headers
                row = {k.strip().lower().replace('\ufeff', ''): v for k, v in raw_row.items()}

                port = row["dstport"].strip()
                protocol = row["protocol"].strip().lower()
                tag = row["tag"].strip()

                if not port or not protocol or not tag:
                    raise ValueError("Missing required value")

                tag_lookup[(port, protocol)] = tag
            except Exception as e:
                print(f"Skipping malformed row {row_num}: {e}")

    return tag_lookup


def process_flow_logs(log_file, tag_lookup):
    tag_counts = defaultdict(int)
    port_protocol_counts = defaultdict(int)

    with open(log_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 14 or parts[0] != '2':
                continue  # Only support version 2 logs

            dstport = parts[6]
            protocol_num = parts[7]
            protocol = PROTOCOL_MAP.get(protocol_num, protocol_num).lower()

            key = (dstport, protocol)
            tag = tag_lookup.get(key, "Untagged")

            tag_counts[tag] += 1
            port_protocol_counts[key] += 1

    return tag_counts, port_protocol_counts

def write_tag_counts(tag_counts, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Tag", "Count"])

        # Separate "Untagged" and sort the rest
        sorted_tags = sorted((k, v) for k, v in tag_counts.items() if k.lower() != "untagged")
        untagged = [("Untagged", tag_counts["Untagged"])] if "Untagged" in tag_counts else []

        for tag, count in sorted_tags + untagged:
            writer.writerow([tag, count])

def write_port_protocol_counts(port_protocol_counts, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Port", "Protocol", "Count"])
        for (port, protocol), count in sorted(port_protocol_counts.items()):
            writer.writerow([port, protocol, count])

def main():
    if len(sys.argv) != 4:
        print("Usage: python flow_tagger.py <flow_log_file> <lookup_csv> <output_folder>")
        sys.exit(1)

    log_file = sys.argv[1]
    lookup_file = sys.argv[2]
    output_folder = sys.argv[3]

    os.makedirs(output_folder, exist_ok=True)

    tag_lookup = load_tag_lookup(lookup_file)
    tag_counts, port_protocol_counts = process_flow_logs(log_file, tag_lookup)

    write_tag_counts(tag_counts, os.path.join(output_folder, 'tag_counts.csv'))
    write_port_protocol_counts(port_protocol_counts, os.path.join(output_folder, 'port_protocol_counts.csv'))
    print("Done. Output written to:", output_folder)

if __name__ == "__main__":
    main()
