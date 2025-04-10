import json
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Optional,
    TypeVar,
    Union,
)
from uuid import UUID

from pydantic import BaseModel, Field, create_model

from syft_llm_router.schema2.type_utils import annotation_as_string, is_optional_type

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


class OpenSpecModelGenerator:
    """Parser and generator for OpenSpec schema files."""

    def __init__(self, spec_path: Union[str, Path]) -> None:
        """Initialize the OpenSpec schema parser.

        Args:
            spec_path: Path to the OpenSpec JSON file
        """
        self.spec_path = Path(spec_path)
        self.spec_data = self._load_spec()
        self.components = self.spec_data.get("components", {})
        self.schemas = self.components.get("schemas", {})
        # Extract nested schemas
        self._extract_nested_schemas()
        # Track generated enums to avoid duplicates
        self.generated_enums: dict[str, type[Enum]] = {}
        # Track dependencies between schemas
        self.dependencies: dict[str, set[str]] = {}
        # Track generated models to avoid duplicates
        self.generated_models: dict[str, type[BaseModel]] = {}

    def _load_spec(self) -> dict[str, Any]:
        """Load and parse the OpenSpec JSON file.

        Returns:
            Dict containing the parsed spec data
        """
        with open(self.spec_path) as f:
            return json.load(f)

    def _extract_nested_schemas(self) -> None:
        """Extract nested schema definitions and add them to the schemas dictionary."""
        for schema_name, schema in list(self.schemas.items()):
            # Check for nested schema definitions
            for key, value in schema.items():
                if (
                    isinstance(value, dict)
                    and "type" in value
                    and key not in self.schemas
                ):
                    # This looks like a nested schema definition
                    self.schemas[key] = value

    def _get_python_type(self, schema: dict[str, Any]) -> type[Any]:
        """Convert OpenSpec types to Python types.

        Args:
            schema: OpenSpec schema definition

        Returns:
            Python type corresponding to the schema
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        # Get the base type
        base_type = type_mapping.get(schema.get("type"), Any)

        # Check for special formats
        if schema.get("type") == "string" and schema.get("format") == "uuid":
            return UUID

        return base_type

    def _resolve_reference(self, ref: str) -> dict[str, Any]:
        """Resolve a reference to a schema.

        Args:
            ref: Reference string (e.g., "#/components/schemas/Usage")

        Returns:
            The referenced schema
        """
        parts = ref.split("/")
        current = self.spec_data

        for part in parts[1:]:  # Skip the first part (#)
            if part.isdigit():
                current = current[int(part)]
            else:
                current = current.get(part, {})

        return current

    def _create_enum_class(
        self, name: str, values: list[str], description: str = ""
    ) -> type[Enum]:
        """Create an enum class from a list of values.

        Args:
            name: Name of the enum class
            values: List of enum values
            description: Description of the enum class

        Returns:
            Generated enum class
        """
        # Check if we've already generated this enum
        if name in self.generated_enums:
            return self.generated_enums[name]

        # Create a new enum class using the standard Enum creation pattern
        enum_class = Enum(name, {v.upper(): v for v in values}, type=str)

        # Set the docstring
        enum_class.__doc__ = description

        # Store the enum class for reuse
        self.generated_enums[name] = enum_class

        return enum_class

    def _to_pascal_case(self, name: str) -> str:
        """Convert a string to PascalCase.

        Args:
            name: String to convert

        Returns:
            String in PascalCase
        """
        # Handle snake_case
        if "_" in name:
            return "".join(word.capitalize() for word in name.split("_"))
        # Handle camelCase
        elif name and name[0].islower():
            return name[0].upper() + name[1:]
        # Already PascalCase or empty
        return name

    def _analyze_dependencies(self) -> None:
        """Analyze dependencies between schemas to determine generation order."""
        for schema_name, schema in self.schemas.items():
            self.dependencies[schema_name] = set()

            # Skip enum schemas
            if schema.get("type") == "string" and "enum" in schema:
                continue

            properties = schema.get("properties", {})
            for prop_name, prop in properties.items():
                # Check for references in properties
                if "$ref" in prop:
                    ref_name = prop["$ref"].split("/")[-1]
                    self.dependencies[schema_name].add(ref_name)

                # Check for references in array items
                if (
                    prop.get("type") == "array"
                    and "items" in prop
                    and "$ref" in prop["items"]
                ):
                    ref_name = prop["items"]["$ref"].split("/")[-1]
                    self.dependencies[schema_name].add(ref_name)

    def _get_generation_order(self) -> list[str]:
        """Determine the order in which to generate schemas.

        Returns:
            List of schema names in generation order
        """
        # First, analyze dependencies
        self._analyze_dependencies()

        # Start with schemas that have no dependencies
        result = []
        remaining = set(self.schemas.keys())

        # First add all enum schemas
        for schema_name, schema in self.schemas.items():
            if schema.get("type") == "string" and "enum" in schema:
                result.append(schema_name)
                remaining.remove(schema_name)

        # Then add schemas with no dependencies
        while remaining:
            # Find schemas with no remaining dependencies
            ready = {
                name
                for name in remaining
                if not self.dependencies[name]
                or self.dependencies[name].issubset(set(result))
            }

            if not ready:
                # If no schemas are ready, we have a circular dependency
                # Just add the remaining schemas in any order
                result.extend(remaining)
                break

            # Add ready schemas to the result
            result.extend(ready)
            remaining -= ready

            # Remove these schemas from other schemas' dependencies
            for name in remaining:
                self.dependencies[name] -= ready

        return result

    def _get_collection_type_hint(self, prop: dict[str, Any]) -> str:
        """Get a proper type hint for collection types.

        Args:
            prop: Property schema definition

        Returns:
            Type hint string for the collection
        """
        if prop.get("type") == "array" and "items" in prop:
            items = prop["items"]
            if "$ref" in items:
                ref_name = items["$ref"].split("/")[-1]
                return f"List[{ref_name}]"
            elif "type" in items:
                item_type = self._get_python_type(items).__name__
                return f"List[{item_type}]"
            else:
                return "List"
        elif prop.get("type") == "object":
            if "additionalProperties" in prop:
                additional_props = prop["additionalProperties"]
                if isinstance(additional_props, dict) and "type" in additional_props:
                    prop_type = self._get_python_type(additional_props).__name__
                    return f"Dict[str, {prop_type}]"
                elif isinstance(additional_props, dict) and "$ref" in additional_props:
                    ref_name = additional_props["$ref"].split("/")[-1]
                    return f"Dict[str, {ref_name}]"
            return "Dict"
        return ""

    def _process_property(
        self, name: str, prop: dict[str, Any], required: bool = False
    ) -> tuple[type[Any], Field]:
        """Process a single property from the schema.

        Args:
            name: Property name
            prop: Property schema definition
            required: Whether the property is required

        Returns:
            Tuple of (type, field) for create_model
        """
        # Get the description
        description = prop.get("description", "")

        # Check if this is an enum
        if "enum" in prop:
            # Create a proper enum name in PascalCase
            enum_name = self._to_pascal_case(name)
            enum_class = self._create_enum_class(enum_name, prop["enum"], description)
            field_type = enum_class
        else:
            field_type = self._get_python_type(prop)

        # Handle array types
        if prop.get("type") == "array" and "items" in prop:
            items = prop["items"]
            if "$ref" in items:
                ref_name = items["$ref"].split("/")[-1]
                field_type = list[self._generate_model(ref_name)]
            else:
                field_type = list[self._get_python_type(items)]

        # Handle object types with $ref
        if "$ref" in prop:
            ref_name = prop["$ref"].split("/")[-1]
            field_type = self._generate_model(ref_name)

        # Create field with validation
        if required or prop.get("required", False):
            # For required fields, use Ellipsis (...) as the default value
            field = Field(description=description)
        else:
            # For optional fields, use None as default and wrap in Optional
            # Check if the type is already Optional
            if not is_optional_type(field_type):
                field_type = Optional[field_type]
            field = Field(default=None, description=description)

        return field_type, field

    def _generate_model(self, schema_name: str) -> type[BaseModel]:
        """Generate a Pydantic model from a schema.

        Args:
            schema_name: Name of the schema to generate

        Returns:
            Generated Pydantic model class
        """
        if schema_name in self.generated_models:
            return self.generated_models[schema_name]

        schema = self.schemas[schema_name]
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        description = schema.get("description", "")

        # Process all properties to get field types and fields
        fields: dict[str, tuple[type[Any], Field]] = {}
        for prop_name, prop in properties.items():
            field_type, field = self._process_property(
                prop_name, prop, prop_name in required
            )
            fields[prop_name] = (field_type, field)

        # Create the model using create_model
        model = create_model(schema_name, **fields, __doc__=description)

        # Store the model for reuse
        self.generated_models[schema_name] = model

        return model

    def generate_models(self) -> dict[str, type[Union[BaseModel, Enum]]]:
        """Generate all Pydantic models from the spec.

        Returns:
            Dictionary mapping schema names to generated model classes
        """
        models: dict[str, type[Union[BaseModel, Enum]]] = {}

        # First, scan for enum properties and create enum classes
        for schema_name, schema in self.schemas.items():
            properties = schema.get("properties", {})
            for prop_name, prop in properties.items():
                if "enum" in prop:
                    # Create a proper enum name in PascalCase
                    enum_name = self._to_pascal_case(prop_name)
                    if enum_name not in models:
                        enum_values = prop["enum"]
                        enum_class = self._create_enum_class(
                            enum_name, enum_values, prop.get("description", "")
                        )
                        models[enum_name] = enum_class

        # Then generate models in the correct order
        generation_order = self._get_generation_order()
        for schema_name in generation_order:
            if schema_name not in models:  # Skip enums we've already generated
                try:
                    models[schema_name] = self._generate_model(schema_name)
                except Exception as e:
                    print(f"Error generating model {schema_name}: {e}")

        return models

    def generate_schema_file(self, output_path: Union[str, Path]) -> None:
        """Generate a Python file containing all the models.

        Args:
            output_path: Path where the generated schema file should be written
        """
        output_path = Path(output_path)
        models = self.generate_models()

        imports = [
            "from enum import Enum",
            "from typing import List, Optional",
            "from uuid import UUID",
            "from pydantic import BaseModel",
            "",
        ]

        model_code = []

        # First, add all enum classes
        for name, model in models.items():
            if isinstance(model, type) and issubclass(model, Enum) and model != Enum:
                model_code.extend(
                    [
                        f"class {name}(str, Enum):",
                        f'    """{model.__doc__ or ""}"""',
                        "",
                    ]
                )

                # Add enum values
                for value in model:
                    model_code.extend(
                        [
                            f"    {value.name} = {repr(value.value)}",
                            "",
                        ]
                    )

        # Then, add all model classes
        for name, model in models.items():
            if not (
                isinstance(model, type) and issubclass(model, Enum) and model != Enum
            ):
                # Get model fields
                fields = []
                for field_name, field_info in model.model_fields.items():
                    field_type = field_info.annotation

                    # Use annotation_as_string to properly format the type
                    field_type_str = annotation_as_string(field_type)

                    # Get the description
                    description = field_info.description or ""

                    # Add description as a comment if it exists
                    if description:
                        fields.append(f"    # {description}")

                    # Check if this is a required field
                    if field_info.is_required():
                        # For required fields, don't specify a default value
                        fields.append(f"    {field_name}: {field_type_str}")
                    else:
                        # For optional fields, use None as default
                        fields.append(f"    {field_name}: {field_type_str} = None")

                # Get the class docstring
                class_docstring = model.__doc__ or ""

                # Add the model class with its fields
                model_code.extend(
                    [
                        f"class {name}(BaseModel):",
                        f'    """{class_docstring}"""',
                        "",
                        *fields,
                        "",
                    ]
                )

        with open(output_path, "w") as f:
            f.write("\n".join(imports + model_code))


if __name__ == "__main__":
    spec_path = Path(__file__).parent.parent / "specs" / "llm-spec.json"
    generator = OpenSpecModelGenerator(spec_path)
    models = generator.generate_models()
    generator.generate_schema_file(Path(__file__).parent / "schema3.py")
