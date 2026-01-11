"""
Tests for password security utilities.
"""
import pytest
from app.core.security import hash_password, verify_password, validate_password


def test_hash_password():
    """Test password hashing."""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    assert hashed is not None
    assert hashed != password
    assert len(hashed) > 20


def test_verify_password():
    """Test password verification."""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_validate_password_strong():
    """Test validation of strong password."""
    is_valid, errors = validate_password("StrongPass123!")
    assert is_valid is True
    assert len(errors) == 0


def test_validate_password_too_short():
    """Test validation of short password."""
    is_valid, errors = validate_password("Short1!")
    assert is_valid is False
    assert any("at least" in error for error in errors)


def test_validate_password_no_uppercase():
    """Test validation without uppercase."""
    is_valid, errors = validate_password("lowercase123!")
    assert is_valid is False
    assert any("uppercase" in error for error in errors)


def test_validate_password_no_lowercase():
    """Test validation without lowercase."""
    is_valid, errors = validate_password("UPPERCASE123!")
    assert is_valid is False
    assert any("lowercase" in error for error in errors)


def test_validate_password_no_numbers():
    """Test validation without numbers."""
    is_valid, errors = validate_password("NoNumbers!")
    assert is_valid is False
    assert any("number" in error for error in errors)


def test_validate_password_no_special():
    """Test validation without special characters."""
    is_valid, errors = validate_password("NoSpecial123")
    assert is_valid is False
    assert any("special" in error for error in errors)
