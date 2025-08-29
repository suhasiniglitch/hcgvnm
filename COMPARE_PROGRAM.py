import csv
import json
import re
import ast
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, timezone
from typing import Any, Dict, List, Tuple, Union

# ---------- Helpers: parsing & coercion ----------

INT32_MIN, INT32_MAX = -(2**31), 2**31 - 1
INT64_MIN, INT64_MAX = -(2**63), 2**63 - 1

BOOL_TRUE = {"true", "1", "yes", "y", "t"}
BOOL_FALSE = {"false", "0", "no", "n", "f"}

ISO_DATE_FORMATS = ["%Y-%m-%d"]
ISO_DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
]

def is_empty(value: str) -> bool:
    return value is None or value == "" or str(value).strip() == ""

def parse_bool(s: str) -> Union[bool, None]:
    s_lower = str(s).strip().lower()
    if s_lower in BOOL_TRUE:
        return True
    if s_lower in BOOL_FALSE:
        return False
    return None

def parse_int(s: str) -> Union[int, None]:
    try:
        return int(str(s).strip())
    except Exception:
        return None

def parse_float(s: str) -> Union[float, None]:
    try:
        return float(str(s).strip())
    except Exception:
        return None

def parse_decimal_str(s: str) -> Union[Decimal, None]:
    try:
        return Decimal(str(s).strip())
    except (InvalidOperation, ValueError):
        return None

def count_decimal_digits(x: Decimal) -> Tuple[int, int]:
    """
    Returns (precision, scale):
      precision = total digits (without sign and decimal point)
      scale = digits to the right of the decimal point
    """
    tup = x.as_tuple()
    digits = len(tup.digits)
    scale = -tup.exponent if tup.exponent < 0 else 0
    # remove leading zeros in the integer part from precision count
    # (Avro decimal precision counts all significant digits)
    # We'll compute precision from quantized normalized string
    normalized = x.normalize()  # may use scientific notation
    s = format(normalized, 'f')  # no scientific notation
    s_digits = re.sub(r"[^0-9]", "", s)
    precision = len(s_digits.lstrip('0')) or 1  # at least 1 digit
    return precision, scale

def parse_date(value: str) -> Union[date, None]:
    s = str(value).strip()
    # integer days since epoch
    if re.fullmatch(r"-?\d+", s):
        days = int(s)
        return date(1970, 1, 1).fromordinal(date(1970, 1, 1).toordinal() + days)
    # ISO date
    for fmt in ISO_DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None

def parse_timestamp(value: str, unit: str) -> Union[datetime, None]:
    """
    unit: 'millis' or 'micros'
    Accepts epoch (ms/us) or ISO datetime (with optional timezone).
    """
    s = str(value).strip()
    # epoch
    if re.fullmatch(r"-?\d+", s):
        i = int(s)
        divisor = 1000 if unit == "millis" else 1_000_000
        try:
            return datetime.fromtimestamp(i / divisor, tz=timezone.utc)
        except Exception:
            return None
    # ISO
    for fmt in ISO_DATETIME_FORMATS:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass
    return None

def parse_array(value: str) -> Union[List[Any], None]:
    """
    Accepts either:
      - Python-like list string: "['a', 'b']"
      - Pipe-separated: "a|b|c"
    Returns list or None.
    """
    s = str(value).strip()
    if s.startswith("[") and s.endswith("]"):
        try:
            obj = ast.literal_eval(s)
            if isinstance(obj, list):
                return obj
        except Exception:
            return None
    # pipe separated
    if "|" in s:
        return s.split("|")
    # single item treated as one-element array
    if not is_empty(s):
        return [s]
    return None

def parse_json_object(value: str) -> Union[Dict[str, Any], None]:
    try:
        obj = json.loads(value)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    return None

# ---------- Validation core ----------

def is_nullable(field_type: Any) -> bool:
    return isinstance(field_type, list) and "null" in field_type

def unwrap_union(field_type: Any) -> Any:
    if isinstance(field_type, list):
        # Prefer the first non-null for validation logic;
        # we'll still allow null through separate null checks.
        for t in field_type:
            if t != "null":
                return t
        return "null"
    return field_type

def validate_value(field_schema: Any, raw_value: str, field_name: str) -> List[Tuple[str, str]]:
    """
    Returns a list of errors for this field (empty list if valid).
    Each error is (error_code, message).
    """
    errors: List[Tuple[str, str]] = []

    # Handle nullability / empty values
    nullable = is_nullable(field_schema)
    effective_schema = unwrap_union(field_schema)

    if is_empty(raw_value):
        if nullable:
            return []
        errors.append(("REQUIRED", f"Field '{field_name}' is required but value is empty"))
        return errors

    # Dict = complex/logical
    if isinstance(effective_schema, dict):
        base_type = effective_schema.get("type")
        logical_type = effective_schema.get("logicalType")

        # Logical: date
        if logical_type == "date":
            if parse_date(raw_value) is None:
                errors.append(("TYPE_DATE", f"Invalid date for '{field_name}'; expected YYYY-MM-DD or days since"))
            return errors

        # Logical: timestamp
        if logical_type in ("timestamp-millis", "timestamp-micros"):
            unit = "millis" if logical_type.endswith("millis") else "micros"
            if parse_timestamp(raw_value, unit) is None:
                errors.append(("TYPE_TIMESTAMP", f"Invalid timestamp for '{field_name}'; expected epoch {unit} or ISO datetime"))
            return errors

        # Logical: decimal
        if logical_type == "decimal":
            precision = effective_schema.get("precision")
            scale = effective_schema.get("scale")
            if precision is None or scale is None:
                errors.append(("SCHEMA_DECIMAL", f"Decimal '{field_name}' missing precision/scale in schema"))
                return errors
            dec = parse_decimal_str(raw_value)
            if dec is None:
                errors.append(("TYPE_DECIMAL", f"Invalid decimal for '{field_name}'"))
                return errors
            prec, scl = count_decimal_digits(dec)
            if scl > scale:
                errors.append(("DECIMAL_SCALE", f"Scale {scl} exceeds schema scale {scale} for '{field_name}'"))
            if prec > precision:
                errors.append(("DECIMAL_PRECISION", f"Precision {prec} exceeds schema precision {precision} for '{field_name}'"))
            return errors

        # Array
        if base_type == "array":
            items_schema = effective_schema.get("items", "string")
            arr = parse_array(raw_value)
            if arr is None:
                errors.append(("TYPE_ARRAY", f"Invalid array format for '{field_name}'. Use \"['a','b']\" or 'a|b'"))
                return errors
            # validate each element
            for idx, item in enumerate(arr):
                item_value = "" if item is None else str(item)
                sub_errors = validate_value(items_schema, item_value, f"{field_name}[{idx}]")
                errors.extend(sub_errors)
            return errors

        # Nested record: expect JSON object in cell
        if base_type == "record":
            obj = parse_json_object(raw_value)
            if obj is None:
                errors.append(("TYPE_RECORD", f"Invalid JSON object for nested record '{field_name}'"))
                return errors
            schema_fields = {f["name"]: f["type"] for f in effective_schema.get("fields", [])}
            # check required / extra
            for sf_name, sf_type in schema_fields.items():
                val = obj.get(sf_name, "")
                sub_errs = validate_value(sf_type, "" if val is None else str(val), f"{field_name}.{sf_name}")
                errors.extend(sub_errs)
            # extra keys
            for key in obj.keys():
                if key not in schema_fields:
                    errors.append(("EXTRA_NESTED_FIELD", f"Extra nested field '{field_name}.{key}' not in schema"))
            return errors

        # Fallback to primitive validation
        return validate_value(base_type, raw_value, field_name)

    # Primitive types
    if effective_schema == "string":
        # always valid (CSV is text), unless you want min/max length constraints (not in Avro core)
        return errors

    if effective_schema == "boolean":
        b = parse_bool(raw_value)
        if b is None:
            errors.append(("TYPE_BOOLEAN", f"Invalid boolean for '{field_name}' (accepted: true/false/1/0/yes/no)"))
        return errors

    if effective_schema == "int":
        i = parse_int(raw_value)
        if i is None:
            errors.append(("TYPE_INT", f"Invalid int for '{field_name}'"))
        else:
            if i < INT32_MIN or i > INT32_MAX:
                errors.append(("RANGE_INT", f"Value {i} out of 32-bit int range for '{field_name}'"))
        return errors

    if effective_schema in ("long", "bigint"):
        i = parse_int(raw_value)
        if i is None:
            errors.append(("TYPE_LONG", f"Invalid long for '{field_name}'"))
        else:
            if i < INT64_MIN or i > INT64_MAX:
                errors.append(("RANGE_LONG", f"Value {i} out of 64-bit long range for '{field_name}'"))
        return errors

    if effective_schema == "float":
        x = parse_float(raw_value)
        if x is None:
            errors.append(("TYPE_FLOAT", f"Invalid float for '{field_name}'"))
        return errors

    if effective_schema == "double":
        x = parse_float(raw_value)
        if x is None:
            errors.append(("TYPE_DOUBLE", f"Invalid double for '{field_name}'"))
        return errors

    if effective_schema == "null":
        if not is_empty(raw_value):
            errors.append(("TYPE_NULL", f"Expected null for '{field_name}'"))
        return errors

    # Unknown type
    errors.append(("SCHEMA_TYPE", f"Unsupported schema type '{effective_schema}' for '{field_name}'"))
    return errors

# ---------- Main validation pipeline ----------

def validate_csv_against_avro(schema_path: str, csv_path: str,
                              bad_records_out: str = "bad_records.csv",
                              error_log_out: str = "error_log.csv") -> None:
    # Load schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    fields = schema.get("fields", [])
    schema_field_names = [f["name"] for f in fields]
    schema_types = {f["name"]: f["type"] for f in fields}

    bad_rows: List[Dict[str, Any]] = []
    error_log: List[Dict[str, Any]] = []

    with open(csv_path, "r", encoding="utf-8", newline="") as cf:
        reader = csv.DictReader(cf)

        # Header checks
        csv_field_names = reader.fieldnames or []
        # Missing columns (required by schema but not in CSV)
        for name in schema_field_names:
            if name not in csv_field_names:
                error_log.append({
                    "row_number": 0,
                    "column": name,
                    "error_code": "MISSING_COLUMN",
                    "message": f"Column '{name}' missing from CSV header",
                    "value": ""
                })
        # Extra columns (present in CSV but not in schema)
        for name in csv_field_names:
            if name not in schema_field_names:
                error_log.append({
                    "row_number": 0,
                    "column": name,
                    "error_code": "EXTRA_COLUMN",
                    "message": f"Column '{name}' not defined in schema",
                    "value": ""
                })

        # Validate rows
        for row_idx, row in enumerate(reader, start=2):  # 1=header, so data starts at 2
            row_errors: List[str] = []

            for name in schema_field_names:
                field_schema = schema_types[name]
                raw_value = row.get(name, "")
                val_str = "" if raw_value is None else str(raw_value)

                errors = validate_value(field_schema, val_str, name)
                if errors:
                    for code, msg in errors:
                        error_log.append({
                            "row_number": row_idx,
                            "column": name,
                            "error_code": code,
                            "message": msg,
                            "value": val_str
                        })
                        row_errors.append(f"{name}: {code}")

            # mark row as bad if any error
            if row_errors:
                # Keep original row + error summary
                bad_row = dict(row)
                bad_row["__errors__"] = "; ".join(row_errors)
                bad_rows.append(bad_row)

    # Write bad records
    if bad_rows:
        # ensure consistent columns: CSV cols + __errors__
        out_fields = list(bad_rows[0].keys())
        with open(bad_records_out, "w", encoding="utf-8", newline="") as bf:
            writer = csv.DictWriter(bf, fieldnames=out_fields)
            writer.writeheader()
            for r in bad_rows:
                writer.writerow(r)

    # Write error log
    with open(error_log_out, "w", encoding="utf-8", newline="") as ef:
        writer = csv.DictWriter(ef, fieldnames=["row_number", "column", "error_code", "message", "value"])
        writer.writeheader()
        for e in error_log:
            writer.writerow(e)

    print(f"Validation complete.")
    if bad_rows:
        print(f"- Bad records written to: {bad_records_out} (count: {len(bad_rows)})")
    else:
        print("- No bad records found.")
    print(f"- Error log written to: {error_log_out} (entries: {len(error_log)})")


if __name__ == "__main__":
    validate_csv_against_avro(
        schema_path="SCHEMA.avsc",
        csv_path="generated_output.csv",
        bad_records_out="records_contains_error.csv",
        error_log_out="error_log.csv",
    )
