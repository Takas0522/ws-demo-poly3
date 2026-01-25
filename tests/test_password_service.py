"""Tests for password service."""
import pytest
from app.core.password_service import password_service


class TestPasswordService:
    """Test cases for password service."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        
        hashed = password_service.hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$2b$12$")  # bcrypt with cost 12
    
    def test_verify_correct_password(self):
        """Test verifying correct password."""
        password = "test_password_123"
        hashed = password_service.hash_password(password)
        
        result = password_service.verify_password(password, hashed)
        
        assert result is True
    
    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = password_service.hash_password(password)
        
        result = password_service.verify_password(wrong_password, hashed)
        
        assert result is False
    
    def test_hash_produces_different_hashes(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "test_password_123"
        
        hash1 = password_service.hash_password(password)
        hash2 = password_service.hash_password(password)
        
        # Different hashes due to different salts
        assert hash1 != hash2
        
        # But both should verify the password correctly
        assert password_service.verify_password(password, hash1) is True
        assert password_service.verify_password(password, hash2) is True
