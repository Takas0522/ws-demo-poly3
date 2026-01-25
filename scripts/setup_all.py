#!/usr/bin/env python3
"""
Complete Cosmos DB setup script.

This script runs both container setup and seed data creation:
1. Creates database and containers
2. Seeds initial data (admin user)
"""
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.setup_containers import CosmosDBSetup
from scripts.seed_data import SeedData


def main():
    """Main entry point for complete setup."""
    print("\n" + "=" * 60)
    print("COSMOS DB COMPLETE SETUP")
    print("=" * 60 + "\n")

    try:
        # Step 1: Setup containers
        print("Step 1: Setting up containers...")
        setup = CosmosDBSetup()
        if not setup.setup():
            print("✗ Container setup failed")
            sys.exit(1)

        print("\n")

        # Step 2: Seed data
        print("Step 2: Seeding initial data...")
        seeder = SeedData()
        if not seeder.seed():
            print("✗ Seed data creation failed")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("✓ COMPLETE SETUP FINISHED SUCCESSFULLY!")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\n✗ Fatal error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
