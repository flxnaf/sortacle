# Cloud PostgreSQL Setup Guide

## Overview

Instead of storing data locally on the Raspberry Pi with SQLite, we're uploading all sorting data to a PostgreSQL database on your Vultr server. The website can then query this database directly.

## Architecture

```
┌─────────────────┐
│  Raspberry Pi   │
│                 │
│  detector_ui    │─────┐
│  (sorts items)  │     │
└─────────────────┘     │
                        │ Upload data
                        │ (PostgreSQL)
                        ▼
              ┌─────────────────────┐
              │   Vultr Server      │
              │                     │
              │  ┌───────────────┐  │
              │  │  PostgreSQL   │  │◄────── Website queries
              │  │   Database    │  │        this database
              │  │ (sortacle_db) │  │
              │  └───────────────┘  │
              │                     │
              │  FastAPI Inference  │
              │  Server (port 8000) │
              └─────────────────────┘
```

## Step 1: Install PostgreSQL on Vultr

SSH into your Vultr server:

```bash
ssh root@YOUR_VULTR_IP
```

Install PostgreSQL:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Check status
sudo systemctl status postgresql
```

## Step 2: Create Database and User

```bash
# Switch to postgres user
sudo -u postgres psql

# In the PostgreSQL prompt, run these commands:
```

```sql
-- Create database
CREATE DATABASE sortacle_db;

-- Create user with password (CHANGE THIS PASSWORD!)
CREATE USER sortacle_user WITH PASSWORD 'your_super_secure_password_123';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE sortacle_db TO sortacle_user;

-- Exit
\q
```

## Step 3: Configure PostgreSQL for Remote Access

Allow the Raspberry Pi to connect:

```bash
# Find PostgreSQL version
ls /etc/postgresql/

# Edit postgresql.conf (replace XX with your version, e.g., 14)
sudo nano /etc/postgresql/XX/main/postgresql.conf

# Find this line and change it:
# listen_addresses = 'localhost'
# TO:
listen_addresses = '*'

# Save and exit (Ctrl+X, Y, Enter)
```

Edit access rules:

```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/XX/main/pg_hba.conf

# Add this line at the end:
host    all             all             0.0.0.0/0               md5

# Save and exit
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

## Step 4: Open Firewall Port

```bash
# Allow PostgreSQL port 5432
sudo ufw allow 5432/tcp

# Check firewall status
sudo ufw status
```

## Step 5: Test Connection from Your Mac

Install PostgreSQL client on your Mac:

```bash
brew install postgresql
```

Test connection:

```bash
psql "postgresql://sortacle_user:your_password@VULTR_IP:5432/sortacle_db"
```

If connected successfully, you should see:
```
sortacle_db=>
```

Type `\q` to exit.

## Step 6: Update Raspberry Pi Code

On your **Raspberry Pi**, install the PostgreSQL driver:

```bash
cd ~/projects/sortacle/inference
source venv/bin/activate
pip install psycopg2-binary
```

Set the database connection:

```bash
# Add to ~/.bashrc so it persists
echo 'export DATABASE_URL="postgresql://sortacle_user:your_password@VULTR_IP:5432/sortacle_db"' >> ~/.bashrc
source ~/.bashrc

# Verify it's set
echo $DATABASE_URL
```

## Step 7: Update detector_ui_pro.py

Modify `detector_ui_pro.py` to use `CloudDataLogger` instead of `DataLogger`:

Change this line:
```python
from data_logger import DataLogger
```

To:
```python
from cloud_data_logger import CloudDataLogger as DataLogger
```

That's it! The rest of the code stays the same.

## Step 8: Test It

On Raspberry Pi:

```bash
cd ~/projects/sortacle/inference
git pull origin main
source venv/bin/activate
python3 cloud_data_logger.py  # Test connection
```

If successful, run the detector:

```bash
export CLOUD_INFERENCE_URL="http://VULTR_IP:8000"
python3 detector_ui_pro.py
```

## Step 9: Website Access

The website can now connect directly to the PostgreSQL database:

### Connection Details for Website Team

```
Host: YOUR_VULTR_IP
Port: 5432
Database: sortacle_db
User: sortacle_user
Password: your_password
```

### Example Node.js Connection

```javascript
const { Pool } = require('pg');

const pool = new Pool({
  host: 'VULTR_IP',
  port: 5432,
  database: 'sortacle_db',
  user: 'sortacle_user',
  password: 'your_password'
});

// Query example
async function getStats() {
  const result = await pool.query(`
    SELECT 
      COUNT(*) as total,
      SUM(CASE WHEN is_recyclable THEN 1 ELSE 0 END) as recyclable
    FROM disposal_events
  `);
  return result.rows[0];
}
```

### Example Python Connection

```python
import psycopg2

conn = psycopg2.connect(
    host="VULTR_IP",
    port=5432,
    database="sortacle_db",
    user="sortacle_user",
    password="your_password"
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM disposal_events")
print(f"Total items: {cursor.fetchone()[0]}")
```

## Database Schema

The table structure:

```sql
disposal_events (
    id SERIAL PRIMARY KEY,
    timestamp DOUBLE PRECISION NOT NULL,
    datetime TIMESTAMP NOT NULL,
    item_label TEXT NOT NULL,
    material_category TEXT,
    confidence REAL NOT NULL,
    is_recyclable BOOLEAN NOT NULL,
    bin_id TEXT DEFAULT 'bin_001',
    location TEXT DEFAULT 'unknown',
    image_path TEXT,
    bbox_x1 REAL,
    bbox_y1 REAL,
    bbox_x2 REAL,
    bbox_y2 REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Useful Queries for Website

### Total counts by material
```sql
SELECT material_category, COUNT(*) as count
FROM disposal_events
GROUP BY material_category
ORDER BY count DESC;
```

### Recycling rate
```sql
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN is_recyclable THEN 1 ELSE 0 END) as recyclable,
    ROUND(100.0 * SUM(CASE WHEN is_recyclable THEN 1 ELSE 0 END) / COUNT(*), 1) as rate
FROM disposal_events;
```

### Today's activity
```sql
SELECT COUNT(*) as today_count
FROM disposal_events
WHERE datetime >= CURRENT_DATE;
```

### Hourly breakdown (for heatmap)
```sql
SELECT 
    DATE_TRUNC('hour', datetime) as hour,
    COUNT(*) as count
FROM disposal_events
WHERE datetime >= NOW() - INTERVAL '24 hours'
GROUP BY hour
ORDER BY hour;
```

## Troubleshooting

### Connection refused from Pi

```bash
# Check if PostgreSQL is running on Vultr
sudo systemctl status postgresql

# Check if port 5432 is open
sudo netstat -tulnp | grep 5432
```

### Can't connect remotely

```bash
# Check firewall
sudo ufw status

# Check PostgreSQL config
sudo cat /etc/postgresql/*/main/postgresql.conf | grep listen_addresses
sudo cat /etc/postgresql/*/main/pg_hba.conf | grep "0.0.0.0"
```

### Test from Pi

```bash
# Install PostgreSQL client on Pi
sudo apt install postgresql-client

# Test connection
psql "postgresql://sortacle_user:password@VULTR_IP:5432/sortacle_db" -c "SELECT NOW();"
```

## Security Note

For production, you should:
1. Use a strong password
2. Restrict `pg_hba.conf` to only allow your Pi's IP address instead of `0.0.0.0/0`
3. Use SSL/TLS for database connections
4. Consider using environment variables or secret management for credentials

## Summary

✅ PostgreSQL installed on Vultr server
✅ Database `sortacle_db` created
✅ User `sortacle_user` with password
✅ Remote access enabled
✅ Pi uploads data to cloud
✅ Website can query database directly
✅ No local SQLite storage needed
