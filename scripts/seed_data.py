"""
Seed data script for Auth Service.

This script creates initial seed data including:
- Privileged tenant's global admin user
"""
import sys
import uuid
from datetime import datetime, UTC
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv
import os
import hashlib

# Load environment variables
load_dotenv()


class SeedData:
    """Helper class for seeding initial data."""

    def __init__(self):
        """Initialize the seed data helper."""
        self.endpoint = os.getenv("COSMOSDB_ENDPOINT")
        self.key = os.getenv("COSMOSDB_KEY")
        self.database_name = os.getenv("COSMOSDB_DATABASE", "saas-management-dev")

        if not self.endpoint or not self.key:
            raise ValueError(
                "COSMOSDB_ENDPOINT and COSMOSDB_KEY must be set in environment variables"
            )

        self.client = CosmosClient(self.endpoint, self.key)
        self.database = self.client.get_database_client(self.database_name)
        self.users_container = self.database.get_container_client("users")

    def hash_password(self, password: str) -> str:
        """
        Simple password hashing for demonstration purposes.
        
        Note: In production, use proper password hashing like bcrypt or argon2.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        # Using SHA-256 for demo purposes
        # In production, use bcrypt, argon2, or similar
        return hashlib.sha256(password.encode()).hexdigest()

    def create_admin_user(self):
        """Create the privileged tenant's global admin user."""
        admin_id = "usr_admin_001"
        admin_user = {
            "id": admin_id,
            "loginId": "admin@saas-platform.local",
            "name": "System Administrator",
            "passwordHash": self.hash_password("Admin@123"),  # Default admin password
            "isActive": True,
            "lockedUntil": None,
            "createdAt": datetime.now(UTC).isoformat(),
            "updatedAt": datetime.now(UTC).isoformat(),
        }

        try:
            # Try to read existing user
            try:
                existing_user = self.users_container.read_item(
                    item=admin_id, partition_key=admin_id
                )
                print(f"ℹ Admin user '{admin_user['loginId']}' already exists")
                return existing_user
            except exceptions.CosmosResourceNotFoundError:
                # User doesn't exist, create it
                created_user = self.users_container.create_item(body=admin_user)
                print(f"✓ Created admin user '{admin_user['loginId']}'")
                print(f"  Login ID: {admin_user['loginId']}")
                print(f"  Default Password: Admin@123")
                print(f"  ⚠️  Please change the default password after first login!")
                return created_user

        except exceptions.CosmosHttpResponseError as e:
            print(f"✗ Error creating admin user: {e}")
            raise

    def seed(self):
        """Run the seed data process."""
        print("=" * 60)
        print("Seed Data Creation")
        print("=" * 60)
        print(f"Endpoint: {self.endpoint}")
        print(f"Database: {self.database_name}")
        print("=" * 60)

        try:
            # Create admin user
            self.create_admin_user()

            print("=" * 60)
            print("✓ Seed data created successfully!")
            print("=" * 60)
            return True

        except Exception as e:
            print("=" * 60)
            print(f"✗ Seed data creation failed: {e}")
            print("=" * 60)
            return False


def main():
    """Main entry point."""
    try:
        seeder = SeedData()
        success = seeder.seed()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
