"""
Permissions utilities for checking user access levels.

This module provides functions to check if users have permission to perform
various operations based on the configuration settings and user roles.
"""

from typing import Optional
from backend.config import (
    PERMISSION_READ,
    PERMISSION_CREATE,
    PERMISSION_EDIT,
    PERMISSION_DELETE,
    PERMISSION_RATE,
)
from backend.models.fixed import UserRead


def check_permission_level(
    required_level: str, user: Optional[UserRead] = None
) -> bool:
    """
    Check if a user meets the required permission level.

    Args:
        required_level: One of 'all', 'loggedin', 'admin'
        user: The user to check permissions for (None for anonymous)

    Returns:
        bool: True if user has required permission level
    """
    if required_level == "all":
        return True

    if required_level == "loggedin":
        return user is not None and user.is_active and user.username != "anonymous"

    if required_level == "admin":
        return (
            user is not None
            and user.is_active
            and user.username != "anonymous"
            and (user.is_admin or user.is_super_admin)
        )

    # Default to deny access for unknown permission levels
    return False


def can_read(user: Optional[UserRead] = None) -> bool:
    """Check if user can view/search nodes/edges."""
    return check_permission_level(PERMISSION_READ, user)


def can_create(user: Optional[UserRead] = None) -> bool:
    """Check if user can create nodes/edges."""
    return check_permission_level(PERMISSION_CREATE, user)


def can_edit(user: Optional[UserRead] = None) -> bool:
    """Check if user can edit nodes/edges."""
    return check_permission_level(PERMISSION_EDIT, user)


def can_delete(user: Optional[UserRead] = None) -> bool:
    """Check if user can delete nodes/edges."""
    return check_permission_level(PERMISSION_DELETE, user)


def can_rate(user: Optional[UserRead] = None) -> bool:
    """Check if user can rate/poll nodes/edges."""
    return check_permission_level(PERMISSION_RATE, user)


def can_edit_field_when_draft(user: Optional[UserRead] = None) -> bool:
    """
    Check if user can edit fields when an element has 'draft' status.
    When status is 'draft', apply normal edit permissions (all authorized users can edit).
    """
    return can_edit(user)


def can_edit_field_when_non_draft(
    user: Optional[UserRead] = None, field: str = None
) -> bool:
    """
    Check if user can edit a specific field when an element has non-draft status.

    Non-draft elements have restrictions:
    - Non-admin users cannot edit: title, type, scope, or revert status to draft
    - Non-admin users CAN edit: description, references, tags
    - Admin/Super Admin users can edit all fields

    Args:
        user: The user to check permissions for
        field: The field name being edited (title, type, scope, status, description, references, tags)

    Returns:
        bool: True if user is allowed to edit the field when status is non-draft
    """
    if not can_edit(user):
        return False

    # Admins can always edit
    if user and (user.is_admin or user.is_super_admin):
        return True

    # Non-admins cannot edit restricted fields when status is non-draft
    restricted_fields = {"title", "type", "scope", "status"}
    if field in restricted_fields:
        return False

    # Non-admins can edit other fields
    return True


def can_rate_element(user: Optional[UserRead] = None, status: str = None) -> bool:
    """
    Check if user can rate an element based on its status.

    Rules:
    - If status is 'draft': no-one can rate it
    - If status is non-draft: all authorized users (according to rate permission) can rate it

    Args:
        user: The user to check permissions for
        status: The status of the element (draft, live, realised, unrealised)

    Returns:
        bool: True if user is allowed to rate the element
    """
    if status == "draft":
        return False

    return can_rate(user)


def get_permission_summary(user: Optional[UserRead] = None) -> dict:
    """
    Get a summary of all permissions for a user.
    Useful for frontend to know what UI elements to show.
    """
    return {
        "read": can_read(user),
        "create": can_create(user),
        "edit": can_edit(user),
        "delete": can_delete(user),
        "rate": can_rate(user),
    }
