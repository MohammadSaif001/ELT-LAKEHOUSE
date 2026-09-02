import json
from pathlib import Path

CONTRACTS_DIR = Path(__file__).resolve().parent


def load_contract(schema_file: str) -> dict:
    schema_path = CONTRACTS_DIR / schema_file

    if not schema_path.is_file():
        raise FileNotFoundError(
            f"Schema file '{schema_file}' not found in '{CONTRACTS_DIR}'"
        )
    try:
        with schema_path.open("r", encoding="utf-8") as json_file:
            schema = json.load(json_file)
        return schema
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON schema: path={schema_path}")


def field_extract(schema: dict) -> list:

    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary.")

    properties = schema.get("properties")

    if not isinstance(properties, dict):
        raise ValueError("Schema must be a dictionary.")

    required_fields = set(schema.get("required", []))

    fields: list[dict] = []

    for column_name, definition in properties.items():
        field_type = definition.get("type")

        if isinstance(field_type, list):
            data_type = next((t for t in field_type if t != "null"), None)
        else:
            data_type = field_type

        fields.append({
            "column_name": column_name,
            "data_type": data_type,
            "nullable": data_type,
            "required": column_name in required_fields,
            **{
                key: definition[key]
                for key in ("format", "minimum", "maximum")
                if key in definition
            },
        })

    return fields

