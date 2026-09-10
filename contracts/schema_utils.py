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
        raise TypeError(f"Invalid JSON schema: path={schema_path}")


def field_extract(schema: dict) -> list:

    if not isinstance(schema, dict):
        raise TypeError("Schema must be a dictionary.")

    properties = schema.get("properties")

    if not isinstance(properties, dict):
        raise TypeError("Schema must be a dictionary.")

    required_fields = set(schema.get("required", []))

    fields: list[dict] = []

    for column_name, definition in properties.items():
        if not isinstance(definition, dict):
            raise TypeError(f"Definition for '{column_name}' must be a dictionary.")

        field_type = definition.get("type")

        if isinstance(field_type, list):
            nullable_from_type = "null" in field_type
            data_type = next((t for t in field_type if t != "null"), None)
        else:
            nullable_from_type = field_type == "null"
            data_type = field_type

        raw_nullable = definition.get("nullable", nullable_from_type)

        if not isinstance(raw_nullable, bool):
            raise TypeError(
                f"'nullable' for '{column_name}' must be a boolean, got {type(raw_nullable).__name__}."
            )
        nullable = raw_nullable

        fields.append(
            {
                "column_name": column_name,
                "data_type": data_type,
                "nullable": nullable,
                "required": column_name in required_fields,
                **{
                    key: definition[key]
                    for key in ("format", "minimum", "maximum")
                    if key in definition
                },
            }
        )

    return fields
