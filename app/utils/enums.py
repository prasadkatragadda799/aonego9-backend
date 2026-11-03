"""Parse client-supplied enum values without turning a typo into a 500."""

from enum import Enum
from typing import TypeVar

from fastapi import HTTPException

E = TypeVar("E", bound=Enum)


def parse_enum(enum_cls: type[E], value, field: str = "status") -> E:
    """`EnumClass(value)` that answers 422 with the allowed values instead of
    raising ValueError (an unhandled 500) on unknown input."""
    try:
        return enum_cls(value)
    except ValueError:
        allowed = ", ".join(str(m.value) for m in enum_cls)
        raise HTTPException(status_code=422, detail=f"Invalid {field} '{value}' — expected one of: {allowed}")
