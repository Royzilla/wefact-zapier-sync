# WeFact → Zapier Sync

Syncs debtors and invoices from WeFact to Zapier webhooks.

## Features

- **Two-way sync**: Debtors and invoices go to separate Zapier webhooks
- **Incremental sync**: Only sends new/changed records after first run
- **Full sync option**: Can force sync all data when needed
- **State tracking**: Remembers last sync time in `sync_state.json`
- **Docker support**: Run in container with scheduled sync

## Quick Start (Docker)

```bash
# One-time sync
docker-compose --profile oneshot run --rm wefact-sync python3 sync.py --full

# Scheduled sync (runs every hour)
docker-compose --profile scheduled up -d wefact-sync-scheduled

# Stop scheduled sync
docker-compose --profile scheduled down
```

## Local Setup

```bash
pip install -r requirements.txt
python3 sync.py --full
```

## Usage

### First run (full sync - sends all data)
```bash
python3 sync.py --full
# or with Docker:
docker-compose --profile oneshot run --rm wefact-sync python3 sync.py --full
```

### Regular runs (incremental - only new/changed)
```bash
python3 sync.py
# or with Docker:
docker-compose --profile oneshot run --rm wefact-sync python3 sync.py
```

## Webhooks

| Data Type | Zapier Webhook |
|-----------|----------------|
| Debtors   | `https://hooks.zapier.com/hooks/catch/18377081/uei7n5h/` |
| Invoices  | `https://hooks.zapier.com/hooks/catch/18377081/uei7kn7/` |

## Payload Format

Zapier receives one request per record:
```json
{
  "data_type": "debtors|invoices",
  "sync_time": "2026-02-10T23:05:00",
  "record": {
    "Identifier": "1",
    "DebtorCode": "DB10000",
    "CompanyName": "...",
    ...
  }
}
```

This means your Zap triggers for **each individual record**, making it easier to process/filter in Zapier.

## Files

- `sync.py` - Main sync script
- `sync_state.json` - Tracks last sync time (auto-created, gitignored)
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container definition
- `docker-compose.yml` - Docker Compose setup with scheduled sync option

## Docker Deployment

### Option 1: One-shot (manual runs)
```bash
# Build image
docker-compose build

# Run once
docker-compose --profile oneshot run --rm wefact-sync python3 sync.py --full
```

### Option 2: Scheduled (runs every hour automatically)
```bash
# Start background container
docker-compose --profile scheduled up -d

# View logs
docker-compose logs -f wefact-sync-scheduled

# Stop
docker-compose --profile scheduled down
```

### Option 3: System cron
Add to crontab:
```bash
0 * * * * cd /path/to/wefact-zapier-sync && docker-compose --profile oneshot run --rm wefact-sync python3 sync.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SYNC_INTERVAL` | Seconds between syncs (scheduled mode) | 3600 |

## Sync State

The file `sync_state.json` tracks when each data type was last synced:
```json
{
  "last_sync": {
    "debtors": "2026-02-10T23:02:42",
    "invoices": "2026-02-10T23:02:42"
  }
}
```

Delete this file to force a full sync on next run.
