"""Pydantic models for API Gateway request bodies."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class UsernameRequest(BaseModel):
    """Request body containing a username."""

    username: str


class RoleAssignment(BaseModel):
    """Request body for assigning a role to a user."""

    role: str


class MetadataPatch(BaseModel):
    """Arbitrary metadata payload."""

    model_config = ConfigDict(extra="allow")


class FlagState(BaseModel):
    """Desired state for a feature flag."""

    enabled: bool
