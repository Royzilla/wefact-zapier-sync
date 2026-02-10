# WeFact → Zapier Sync

Syncs debtors and invoices from WeFact to Zapier webhooks.

## Features

- **Two-way sync**: Debtors and invoices go to separate Zapier webhooks
- **Incremental sync**: Only sends new/changed records after first run
- **Full sync option**: Can force sync all data when needed
- **State tracking**: Remembers last sync time in `sync_state.json`
- **Docker support**: Run in container with scheduled sync
- **Web Dashboard**: Monitor sync status and trigger runs from browser

## Quick Start (Docker)

```bash
# One-time sync
docker-compose --profile oneshot run --rm wefact-sync python3 sync.py --full

# Scheduled sync (runs every hour)
docker-compose --profile scheduled up -d

# Dashboard (access at http://localhost:5000)
docker-compose --profile dashboard up -d

# Stop services
docker-compose --profile scheduled down
docker-compose --profile dashboard down
```

## Local Setup

```bash
pip install -r requirements.txt

# Run sync
python3 sync.py --full

# Run dashboard (in another terminal)
python3 dashboard.py
# Then open http://localhost:5000
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

## Dashboard

The web dashboard provides:
- **Sync status** - Last sync times for debtors and invoices
- **Quick actions** - Trigger incremental or full sync from browser
- **Live logs** - View recent sync output
- **Real-time updates** - Auto-refreshes every 30 seconds

Access at `http://localhost:5000` when running the dashboard.

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
- `dashboard.py` - Flask web dashboard
- `templates/dashboard.html` - Dashboard UI
- `sync_state.json` - Tracks last sync time (auto-created, gitignored)
- `sync.log` - Log output (auto-created, gitignored)
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container definition
- `docker-compose.yml` - Docker Compose setup

## Docker Deployment

### Option 1: One-shot (manual runs)
```bash
docker-compose --profile oneshot run --rm wefact-sync python3 sync.py --full
```

### Option 2: Scheduled (runs every hour automatically)
```bash
docker-compose --profile scheduled up -d
docker-compose logs -f wefact-sync-scheduled
docker-compose --profile scheduled down
```

### Option 3: Dashboard (web UI)
```bash
docker-compose --profile dashboard up -d
# Access at http://localhost:5000
docker-compose --profile dashboard down
```

### Option 4: Everything together
```bash
# Run both scheduled sync and dashboard
docker-compose --profile scheduled --profile dashboard up -d
```

### Option 5: System cron
Add to crontab:
```bash
0 * * * * cd /path/to/wefact-zapier-sync && docker-compose --profile oneshot run --rm wefact-sync python3 sync.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SYNC_INTERVAL` | Seconds between syncs (scheduled mode) | 3600 |

## Sync State

The file `sync_state.json` tracks sync history:
```json
{
  "last_sync": {
    "debtors": "2026-02-10T23:02:42",
    "invoices": "2026-02-10T23:02:42"
  },
  "total_runs": 5,
  "debtors_synced": 276,
  "invoices_synced": 668
}
```

Delete this file to force a full sync on next run.
