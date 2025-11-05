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
