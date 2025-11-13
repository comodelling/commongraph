"""
Test the permissions system to ensure it works correctly.
"""

from backend.utils.permissions import (
    check_permission_level,
    can_read,
    can_create,
    can_edit,
    can_delete,
    can_rate,
)
from backend.models.fixed import UserRead


def test_permissions():
    # Test anonymous user (like what get_current_user returns when no token)
    anonymous_user = UserRead(
        username="anonymous", is_active=False, is_admin=False, is_super_admin=False
    )

    # Test logged in regular user
    regular_user = UserRead(
        username="testuser", is_active=True, is_admin=False, is_super_admin=False
    )

    # Test admin user
    admin_user = UserRead(
        username="admin", is_active=True, is_admin=True, is_super_admin=False
    )

    print("Testing permission levels:")
    print(f"Anonymous user can_read: {can_read(anonymous_user)}")
    print(f"Regular user can_read: {can_read(regular_user)}")
    print(f"Admin user can_read: {can_read(admin_user)}")

    print(f"Anonymous user can_create: {can_create(anonymous_user)}")
    print(f"Regular user can_create: {can_create(regular_user)}")
    print(f"Admin user can_create: {can_create(admin_user)}")

    print(f"Anonymous user can_delete: {can_delete(anonymous_user)}")
    print(f"Regular user can_delete: {can_delete(regular_user)}")
    print(f"Admin user can_delete: {can_delete(admin_user)}")

    # Test specific permission levels
    print(
        f"\nTesting 'all' level with anonymous: {check_permission_level('all', anonymous_user)}"
    )
    print(
        f"Testing 'loggedin' level with anonymous: {check_permission_level('loggedin', anonymous_user)}"
    )
    print(
        f"Testing 'loggedin' level with regular user: {check_permission_level('loggedin', regular_user)}"
    )
    print(
        f"Testing 'admin' level with regular user: {check_permission_level('admin', regular_user)}"
    )
    print(
        f"Testing 'admin' level with admin user: {check_permission_level('admin', admin_user)}"
    )


if __name__ == "__main__":
    test_permissions()
