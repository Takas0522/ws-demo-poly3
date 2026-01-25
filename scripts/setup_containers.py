"""
Cosmos DB container setup script.

This script creates the necessary containers for the Auth Service:
- users container: stores user information (partition key: /id)
- login-attempts container: stores login attempt logs (partition key: /loginId)
"""
import asyncio
import sys
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class CosmosDBSetup:
    """Helper class for setting up Cosmos DB containers."""

    def __init__(self):
        """Initialize the Cosmos DB setup."""
        self.endpoint = os.getenv("COSMOSDB_ENDPOINT")
        self.key = os.getenv("COSMOSDB_KEY")
        self.database_name = os.getenv("COSMOSDB_DATABASE", "saas-management-dev")

        if not self.endpoint or not self.key:
            raise ValueError(
                "COSMOSDB_ENDPOINT and COSMOSDB_KEY must be set in environment variables"
            )

        self.client = CosmosClient(self.endpoint, self.key)

    def create_database_if_not_exists(self):
        """Create the database if it doesn't exist."""
        try:
            self.database = self.client.create_database_if_not_exists(id=self.database_name)
            print(f"✓ Database '{self.database_name}' is ready")
            return self.database
        except exceptions.CosmosHttpResponseError as e:
            print(f"✗ Error creating database: {e}")
            raise

    def create_container_if_not_exists(self, container_name: str, partition_key_path: str):
        """
        Create a container if it doesn't exist.

        Args:
            container_name: Name of the container to create
            partition_key_path: Partition key path (e.g., "/id", "/loginId")
        """
        try:
            container = self.database.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path=partition_key_path),
                offer_throughput=400,  # Set RU/s throughput
            )
            print(f"✓ Container '{container_name}' with partition key '{partition_key_path}' is ready")
            return container
        except exceptions.CosmosHttpResponseError as e:
            print(f"✗ Error creating container '{container_name}': {e}")
            raise

    def setup(self):
        """Run the complete setup process."""
        print("=" * 60)
        print("Cosmos DB Container Setup")
        print("=" * 60)
        print(f"Endpoint: {self.endpoint}")
        print(f"Database: {self.database_name}")
        print("=" * 60)

        try:
            # Create database
            self.create_database_if_not_exists()

            # Create containers
            self.create_container_if_not_exists("users", "/id")
            self.create_container_if_not_exists("login-attempts", "/loginId")
            self.create_container_if_not_exists("user-roles", "/userId")
            self.create_container_if_not_exists("user-tenants", "/userId")

            print("=" * 60)
            print("✓ Setup completed successfully!")
            print("=" * 60)
            return True

        except Exception as e:
            print("=" * 60)
            print(f"✗ Setup failed: {e}")
            print("=" * 60)
            return False


def main():
    """Main entry point."""
    try:
        setup = CosmosDBSetup()
        success = setup.setup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
