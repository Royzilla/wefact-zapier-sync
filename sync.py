#!/usr/bin/env python3
"""
WeFact to Zapier Sync
Fetches debtors and invoices from WeFact API and sends to Zapier webhooks.
Supports both full sync and incremental sync (only new/changed records).
"""

import json
import requests
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configuration
WEFACT_API_URL = "https://api.mijnwefact.nl/v2/"
WEFACT_API_KEY = "309db38a9ca280c54bfcfdec4540f28d"

ZAPIER_WEBHOOKS = {
    "debtors": "https://hooks.zapier.com/hooks/catch/18377081/uei7n5h/",
    "invoices": "https://hooks.zapier.com/hooks/catch/18377081/uei7kn7/"
}

STATE_FILE = Path(__file__).parent / "sync_state.json"


class WeFactZapierSync:
    def __init__(self):
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load sync state from file."""
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {"last_sync": {}}
    
    def _save_state(self):
        """Save sync state to file."""
        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def _wefact_request(self, controller: str, action: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the WeFact API."""
        payload = {
            "api_key": WEFACT_API_KEY,
            "controller": controller,
            "action": action
        }
        if params:
            payload.update(params)
        
        response = requests.post(WEFACT_API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    
    def fetch_debtors(self, full_sync: bool = False) -> List[Dict]:
        """Fetch debtors from WeFact."""
        print(f"Fetching debtors... {'(full sync)' if full_sync else '(incremental)'}")
        
        result = self._wefact_request("debtor", "list")
        debtors = result.get("debtors", [])
        
        if not full_sync and "debtors" in self.state["last_sync"]:
            last_sync_time = self.state["last_sync"]["debtors"]
            # Filter only modified since last sync
            debtors = [
                d for d in debtors 
                if d.get("Modified", "") > last_sync_time
            ]
            print(f"  Found {len(debtors)} new/changed debtors since {last_sync_time}")
        else:
            print(f"  Found {len(debtors)} total debtors")
        
        return debtors
    
    def fetch_invoices(self, full_sync: bool = False) -> List[Dict]:
        """Fetch invoices from WeFact."""
        print(f"Fetching invoices... {'(full sync)' if full_sync else '(incremental)'}")
        
        result = self._wefact_request("invoice", "list")
        invoices = result.get("invoices", [])
        
        if not full_sync and "invoices" in self.state["last_sync"]:
            last_sync_time = self.state["last_sync"]["invoices"]
            # Filter only modified since last sync
            invoices = [
                inv for inv in invoices 
                if inv.get("Modified", "") > last_sync_time
            ]
            print(f"  Found {len(invoices)} new/changed invoices since {last_sync_time}")
        else:
            print(f"  Found {len(invoices)} total invoices")
        
        return invoices
    
    def send_to_zapier(self, data_type: str, records: List[Dict]) -> bool:
        """Send records to Zapier webhook."""
        if not records:
            print(f"  No {data_type} to send.")
            return True
        
        webhook_url = ZAPIER_WEBHOOKS.get(data_type)
        if not webhook_url:
            print(f"  Error: No webhook configured for {data_type}")
            return False
        
        print(f"  Sending {len(records)} {data_type} to Zapier...")
        
        # Zapier expects an object, so we wrap the array
        payload = {
            "data_type": data_type,
            "count": len(records),
            "sync_time": datetime.now().isoformat(),
            "records": records
        }
        
        try:
            response = requests.post(webhook_url, json=payload)
            response.raise_for_status()
            print(f"  ✓ Successfully sent {data_type} to Zapier")
            return True
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error sending {data_type}: {e}")
            return False
    
    def sync(self, full_sync: bool = False):
        """Run the sync process."""
        print(f"\n{'='*50}")
        print(f"WeFact → Zapier Sync")
        print(f"Mode: {'FULL SYNC' if full_sync else 'INCREMENTAL'}")
        print(f"Started: {datetime.now().isoformat()}")
        print(f"{'='*50}\n")
        
        # Sync debtors
        debtors = self.fetch_debtors(full_sync=full_sync)
        if self.send_to_zapier("debtors", debtors):
            self.state["last_sync"]["debtors"] = datetime.now().isoformat()
        
        print()
        
        # Sync invoices
        invoices = self.fetch_invoices(full_sync=full_sync)
        if self.send_to_zapier("invoices", invoices):
            self.state["last_sync"]["invoices"] = datetime.now().isoformat()
        
        # Save state
        self._save_state()
        
        print(f"\n{'='*50}")
        print(f"Sync completed: {datetime.now().isoformat()}")
        print(f"{'='*50}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync WeFact data to Zapier")
    parser.add_argument(
        "--full", 
        action="store_true", 
        help="Perform full sync (all records) instead of incremental"
    )
    
    args = parser.parse_args()
    
    sync = WeFactZapierSync()
    sync.sync(full_sync=args.full)


if __name__ == "__main__":
    main()
