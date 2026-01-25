# Scripts Directory

This directory contains utility scripts for setting up and managing the Auth Service Cosmos DB infrastructure.

## Available Scripts

### 1. setup_containers.py

Creates the necessary Cosmos DB containers for the Auth Service.

**Usage:**
```bash
cd /home/runner/work/ws-demo-poly3/ws-demo-poly3
python scripts/setup_containers.py
```

**What it does:**
- Creates the database if it doesn't exist
- Creates the `users` container with partition key `/id`
- Creates the `login-attempts` container with partition key `/loginId`

**Requirements:**
- Environment variables must be set (in `.env` file):
  - `COSMOSDB_ENDPOINT`
  - `COSMOSDB_KEY`
  - `COSMOSDB_DATABASE` (optional, defaults to "saas-management-dev")

### 2. seed_data.py

Seeds initial data into the Auth Service database.

**Usage:**
```bash
cd /home/runner/work/ws-demo-poly3/ws-demo-poly3
python scripts/seed_data.py
```

**What it does:**
- Creates a global administrator user for the privileged tenant
  - Login ID: `admin@saas-platform.local`
  - Default Password: `Admin@123`
  - ⚠️ **Important:** Change the default password after first login!

**Requirements:**
- Containers must already exist (run `setup_containers.py` first)
- Environment variables must be set (in `.env` file)

### 3. setup_all.py

Runs the complete setup process (containers + seed data).

**Usage:**
```bash
cd /home/runner/work/ws-demo-poly3/ws-demo-poly3
python scripts/setup_all.py
```

**What it does:**
1. Runs `setup_containers.py` to create containers
2. Runs `seed_data.py` to create initial data

This is the recommended way to set up the database from scratch.

## Quick Start

1. Copy `.env.example` to `.env` and configure your Cosmos DB credentials:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings:
   ```
   COSMOSDB_ENDPOINT=your-endpoint
   COSMOSDB_KEY=your-key
   COSMOSDB_DATABASE=saas-management-dev
   ```

3. Run the complete setup:
   ```bash
   python scripts/setup_all.py
   ```

## Cosmos DB Emulator (Local Development)

For local development, you can use the Azure Cosmos DB Emulator:

1. Start the Cosmos DB Emulator (Docker):
   ```bash
   docker run -p 8081:8081 -p 10251-10254:10251-10254 \
     mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:latest
   ```

2. Use the default emulator credentials in `.env`:
   ```
   COSMOSDB_ENDPOINT=https://localhost:8081
   COSMOSDB_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
   COSMOSDB_DATABASE=saas-management-dev
   ```

## Troubleshooting

### Script fails with connection error
- Verify that your Cosmos DB instance is running
- Check that `COSMOSDB_ENDPOINT` and `COSMOSDB_KEY` are correct
- If using the emulator, ensure it has fully started (can take a minute)

### Container already exists
- This is normal - the scripts will skip creating containers that already exist
- No data will be lost

### Admin user already exists
- This is normal - the seed script will skip creating the admin user if it already exists
- The existing admin user is preserved
