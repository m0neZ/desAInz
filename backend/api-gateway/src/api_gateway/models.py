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


class StatusResponse(BaseModel):
    """Simple status message."""

    status: str


class TokenResponse(BaseModel):
    """JWT token pair returned on authentication."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PendingRuns(BaseModel):
    """IDs of runs waiting for approval."""

    runs: list[str]


class RoleItem(BaseModel):
    """Role assignment for a single user."""

    username: str
    role: str


class RolesResponse(BaseModel):
    """Paginated list of role assignments."""

    total: int
    items: list[RoleItem]


class RefreshRequest(BaseModel):
    """Request body containing a refresh token."""

    refresh_token: str


class UserResponse(BaseModel):
    """Authenticated username payload."""

    user: str | None


class PurgeResult(BaseModel):
    """Result of a PII purge."""

    status: str
    purged: int


class ApprovalStatus(BaseModel):
    """Approval status for a run."""

    approved: bool
