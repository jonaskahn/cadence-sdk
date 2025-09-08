from typing import Type, TypeVar

_T = TypeVar("_T")


def object_schema(cls: Type[_T]) -> Type[_T]:
    setattr(cls, "__response_kind__", "object")
    return cls


def list_schema(cls: Type[_T]) -> Type[_T]:
    setattr(cls, "__response_kind__", "list")
    return cls
