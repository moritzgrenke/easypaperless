"""Permission models for create operations."""

from pydantic import BaseModel, Field


class PermissionSet(BaseModel):
    users: list[int] = Field(default_factory=list)
    groups: list[int] = Field(default_factory=list)


class SetPermissions(BaseModel):
    view: PermissionSet = Field(default_factory=PermissionSet)
    change: PermissionSet = Field(default_factory=PermissionSet)
