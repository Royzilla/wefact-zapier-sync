# WeFact → Zapier Sync

Syncs debtors and invoices from WeFact to Zapier webhooks.

## Features

- **Two-way sync**: Debtors and invoices go to separate Zapier webhooks
- **Incremental sync**: Only sends new/changed records after first run
- **Full sync option**: Can force sync all data when needed
- **State tracking**: Remembers last sync time in `sync_state.json`

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### First run (full sync - sends all data)
```bash
python sync.py --full
```

### Regular runs (incremental - only new/changed)
```bash
python sync.py
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
- `sync_state.json` - Tracks last sync time (auto-created)
- `requirements.txt` - Python dependencies

## Automation

Set up a cron job to run every hour:
```bash
0 * * * * cd /path/to/wefact-zapier-sync && python sync.py
```
