#!/usr/bin/env python3
"""Delete existing admin user to allow recreation with updated roles."""
import os
import sys
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("COSMOSDB_ENDPOINT")
key = os.getenv("COSMOSDB_KEY")
database_name = os.getenv("COSMOSDB_DATABASE", "saas-management-dev")

client = CosmosClient(endpoint, key)
database = client.get_database_client(database_name)
users_container = database.get_container_client("users")

admin_id = "user-admin-001"

try:
    # Delete the existing admin user
    users_container.delete_item(item=admin_id, partition_key=admin_id)
    print(f"✓ Deleted existing admin user: {admin_id}")
except exceptions.CosmosResourceNotFoundError:
    print(f"ℹ Admin user '{admin_id}' does not exist")
except Exception as e:
    print(f"✗ Error deleting admin user: {e}")
    sys.exit(1)
