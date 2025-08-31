import json
import csv
import random
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from typing import Any

# --- Utility to generate human-readable sample values based on Avro type ---
def generate_sample_value(field_type: Any) -> Any:
    """Generate a sample value based on Avro field type."""

    # Handle union types like ["null", "string"]
    if isinstance(field_type, list):
        non_null_types = [t for t in field_type if t != "null"]
        if not non_null_types:
            return None
        return generate_sample_value(non_null_types[0])

    # Handle dict types (logical, decimal, array, nested)
    if isinstance(field_type, dict):
        base_type = field_type.get("type")
        logical_type = field_type.get("logicalType")

        # --- Date (convert days since epoch → YYYY-MM-DD) ---
        if logical_type == "date":
            days_since_epoch = random.randint(18000, 19000)
            return (datetime(1970, 1, 1, tzinfo=UTC) + timedelta(days=days_since_epoch)).strftime("%Y-%m-%d")

        # --- Timestamp (convert millis/micros → YYYY-MM-DD HH:MM:SS) ---
        if logical_type in ["timestamp-millis", "timestamp-micros"]:
            now = datetime.now(UTC)
            timestamp = int(now.timestamp() * (1000 if logical_type.endswith("millis") else 1_000_000))
            return datetime.fromtimestamp(
                timestamp / (1000 if logical_type.endswith("millis") else 1_000_000),
                UTC
            ).strftime("%Y-%m-%d %H:%M:%S")

        # --- Decimal ---
        if logical_type == "decimal":
            precision = field_type.get("precision")
            scale = field_type.get("scale")
            if precision is None or scale is None:
                raise ValueError(f"Decimal field missing precision/scale: {field_type}")

            max_value = 10 ** (precision - scale) - 1
            random_val = random.uniform(0, max_value)
            return str(round(Decimal(random_val), scale))

        # --- Array (convert to Python-like list string) ---
        if base_type == "array":
            item_type = field_type.get("items", "string")
            items = [generate_sample_value(item_type) for _ in range(random.randint(1, 3))]
            return repr(items)  # Ensures output like "['sample_text', 'sample_text']"

        # --- Nested record ---
        if base_type == "record":
            return {
                subfield["name"]: generate_sample_value(subfield["type"])
                for subfield in field_type.get("fields", [])
            }

        return generate_sample_value(base_type)

    # --- Primitive Types ---
    if field_type == "string":
        return "sample_text"
    elif field_type == "int":
        return random.randint(1, 100)
    elif field_type in ["long", "bigint"]:
        return random.randint(1000, 100000)
    elif field_type == "float":
        return round(random.uniform(1, 100), 2)
    elif field_type == "double":
        return round(random.uniform(1, 100), 3)
    elif field_type == "boolean":
        return random.choice([True, False])
    elif field_type == "null":
        return None
    else:
        return f"unsupported_{field_type}"

# --- Main function to generate human-readable CSV ---
def generate_csv_from_avro_schema(schema_file: str, output_csv: str, record_count: int = 10):
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    fields = schema.get("fields", [])
    field_names = [f["name"] for f in fields]

    with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names, delimiter=";")  # <-- CHANGED HERE
        writer.writeheader()

        for _ in range(record_count):
            row = {}
            for field in fields:
                row[field["name"]] = generate_sample_value(field["type"])
            writer.writerow(row)

    print(f"file '{output_csv}' generated with {record_count} records.")

# --- Example Usage ---
if __name__ == "__main__":
    schema_path = "SCHEMA5.avsc"  # Replace with your schema file
    output_csv_path = "SCHEMA5_output.csv"
    generate_csv_from_avro_schema(schema_path, output_csv_path, record_count=4)
