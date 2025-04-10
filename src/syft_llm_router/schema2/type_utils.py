from types import NoneType
from typing import (
    Any,
    Optional,
    Union,
    get_args,
    get_origin,
)

from pydantic import BaseModel


def is_optional_type(t: Any) -> bool:
    """Check if a type is Optional[T]."""
    return get_origin(t) is Union and type(None) in get_args(t)


def annotation_as_string(annotation):
    """
    Convert a typing annotation to its string representation.

    Args:
        annotation: A typing annotation (Union, List, etc.)

    Returns:
        str: String representation of the annotation
    """
    # Handle None or NoneType
    if annotation is None:
        return "None"
    if annotation is NoneType or annotation is type(None):
        return "None"

    # Get origin and arguments
    origin = get_origin(annotation)
    args = get_args(annotation)

    # Handle basic types
    if origin is None:
        if annotation is Any:
            return "Any"
        if hasattr(annotation, "__name__"):
            return annotation.__name__
        return str(annotation)

    # Handle Union
    if origin is Union:
        # Check if Optional (Union with NoneType)
        has_none = NoneType in args or type(None) in args
        non_none_args = [
            arg for arg in args if arg is not NoneType and arg is not type(None)
        ]

        if has_none:
            if len(non_none_args) == 1:
                # Simple Optional[Type]
                return f"Optional[{annotation_as_string(non_none_args[0])}]"
            else:
                # Optional[Union[...]]
                inner_types = ", ".join(
                    annotation_as_string(arg) for arg in non_none_args
                )
                return f"Optional[Union[{inner_types}]]"
        else:
            # Regular Union
            inner_types = ", ".join(annotation_as_string(arg) for arg in args)
            return f"Union[{inner_types}]"

    # Handle List, Dict, Set, etc.
    if origin in (list, list):
        if not args:
            return "List"
        return f"List[{annotation_as_string(args[0])}]"

    if origin in (dict, dict):
        if not args or len(args) != 2:
            return "Dict"
        return f"Dict[{annotation_as_string(args[0])}, {annotation_as_string(args[1])}]"

    if origin in (set, set):
        if not args:
            return "Set"
        return f"Set[{annotation_as_string(args[0])}]"

    if origin in (tuple, tuple):
        if not args:
            return "Tuple"
        inner_types = ", ".join(annotation_as_string(arg) for arg in args)
        return f"Tuple[{inner_types}]"

    # Handle other parameterized generics
    if args:
        origin_name = getattr(origin, "__name__", str(origin).replace("typing.", ""))
        inner_types = ", ".join(annotation_as_string(arg) for arg in args)
        return f"{origin_name}[{inner_types}]"

    # Fallback
    return str(annotation).replace("typing.", "")


def get_field_type_hints(cls: type[BaseModel]) -> dict[str, str]:
    """
    Get type hints for all fields in a Pydantic model.

    Args:
        cls: Pydantic model class

    Returns:
        Dict[str, str]: Dictionary of field names to their type string representations
    """
    return {
        name: annotation_as_string(field.annotation)
        for name, field in cls.model_fields.items()
    }


# Example usage:
if __name__ == "__main__":
    from pydantic import BaseModel

    class B(BaseModel):
        x: Union[list[str], int, Any, None]
        y: Optional[dict[str, list[int]]]
        z: int

    print(B.model_fields["x"].annotation)
    print(
        annotation_as_string(B.model_fields["x"].annotation)
    )  # Should output: Optional[Union[List[str], int, Any]]

    print(B.model_fields["y"].annotation)
    print(
        annotation_as_string(B.model_fields["y"].annotation)
    )  # Should output: Optional[Dict[str, List[int]]]

    print(B.model_fields["z"].annotation)
    print(annotation_as_string(B.model_fields["z"].annotation))  # Should output: int
