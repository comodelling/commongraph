#!/usr/bin/env python3
"""
Test script to verify the super admin functionality works correctly.
Run this after applying the database migration.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.models.fixed import User, UserRead, UserCreate


def test_user_models():
    """Test that our updated user models work correctly."""

    print("Testing User model creation...")

    # Test UserCreate with new field
    user_create = UserCreate(
        username="testuser",
        password="password123",
        security_question="What is your favorite color?",
        security_answer="blue",
        is_super_admin=True,
    )
    print(
        f"✅ UserCreate: {user_create.username}, super_admin: {user_create.is_super_admin}"
    )

    # Test UserRead with new field
    user_read = UserRead(
        username="testuser", is_active=True, is_admin=True, is_super_admin=True
    )
    print(
        f"✅ UserRead: {user_read.username}, admin: {user_read.is_admin}, super_admin: {user_read.is_super_admin}"
    )

    # Test User model
    user = User(
        username="testuser",
        password="hashed_password",
        security_question="What is your favorite color?",
        security_answer="blue",
        is_super_admin=True,
    )
    print(f"✅ User: {user.username}, super_admin: {user.is_super_admin}")

    print("\n🎉 All user model tests passed!")


if __name__ == "__main__":
    test_user_models()
