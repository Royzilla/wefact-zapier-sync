#!/usr/bin/env python3
"""
WeFact to Zapier Sync
Fetches debtors and invoices from WeFact API and sends to Zapier webhooks.
Supports both full sync and incremental sync (only new/changed records).
"""

import json
import requests
import os
import sys
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
LOG_FILE = Path(__file__).parent / "sync.log"

# Setup logging to both console and file
class Logger:
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.terminal = sys.stdout
        
    def write(self, message):
        self.terminal.write(message)
        self.terminal.flush()
        with open(self.log_file, 'a') as f:
            f.write(message)
    
    def flush(self):
        self.terminal.flush()

sys.stdout = Logger(LOG_FILE)


class WeFactZapierSync:
    def __init__(self):
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load sync state from file."""
        if STATE_FILE.exists():
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        return {"last_sync": {}, "total_runs": 0, "debtors_synced": 0, "invoices_synced": 0}
    
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
    
    def fetch_debtors(self, full_sync: bool = False, full_details: bool = False) -> List[Dict]:
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
        
        # Fetch full details if requested
        if full_details:
            print(f"  Fetching full details for each debtor...")
            detailed_debtors = []
            for i, debtor in enumerate(debtors, 1):
                try:
                    detail = self._wefact_request(
                        "debtor", 
                        "show", 
                        {"Identifier": debtor["Identifier"]}
                    )
                    if "debtor" in detail:
                        detailed_debtors.append(detail["debtor"])
                    else:
                        # Fall back to list data if show fails
                        detailed_debtors.append(debtor)
                    
                    if i % 20 == 0:
                        print(f"    ...fetched {i}/{len(debtors)} details")
                except Exception as e:
                    print(f"    ✗ Error fetching debtor {debtor.get('Identifier')}: {e}")
                    detailed_debtors.append(debtor)
            
            debtors = detailed_debtors
            print(f"  ✓ Fetched full details for {len(debtors)} debtors")
        
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
        """Send records to Zapier webhook one by one."""
        if not records:
            print(f"  No {data_type} to send.")
            return True
        
        webhook_url = ZAPIER_WEBHOOKS.get(data_type)
        if not webhook_url:
            print(f"  Error: No webhook configured for {data_type}")
            return False
        
        print(f"  Sending {len(records)} {data_type} to Zapier (one by one)...")
        
        success_count = 0
        for i, record in enumerate(records, 1):
            # Add metadata to each record
            payload = {
                "data_type": data_type,
                "sync_time": datetime.now().isoformat(),
                "record": record
            }
            
            try:
                response = requests.post(webhook_url, json=payload)
                response.raise_for_status()
                success_count += 1
                if i % 50 == 0:
                    print(f"    ...sent {i}/{len(records)}")
            except requests.exceptions.RequestException as e:
                print(f"    ✗ Error sending record {i} ({record.get('Identifier', 'unknown')}): {e}")
        
        print(f"  ✓ Successfully sent {success_count}/{len(records)} {data_type} to Zapier")
        return success_count == len(records)
    
    def sync(self, full_sync: bool = False, full_details: bool = False):
        """Run the sync process."""
        print(f"\n{'='*50}")
        print(f"WeFact → Zapier Sync")
        print(f"Mode: {'FULL SYNC' if full_sync else 'INCREMENTAL'}")
        print(f"Debtor details: {'FULL' if full_details else 'BASIC'}")
        print(f"Started: {datetime.now().isoformat()}")
        print(f"{'='*50}\n")
        
        total_debtors = 0
        total_invoices = 0
        
        # Sync debtors
        debtors = self.fetch_debtors(full_sync=full_sync, full_details=full_details)
        if self.send_to_zapier("debtors", debtors):
            self.state["last_sync"]["debtors"] = datetime.now().isoformat()
            total_debtors = len(debtors)
            self.state["debtors_synced"] = self.state.get("debtors_synced", 0) + total_debtors
        
        print()
        
        # Sync invoices
        invoices = self.fetch_invoices(full_sync=full_sync)
        if self.send_to_zapier("invoices", invoices):
            self.state["last_sync"]["invoices"] = datetime.now().isoformat()
            total_invoices = len(invoices)
            self.state["invoices_synced"] = self.state.get("invoices_synced", 0) + total_invoices
        
        # Update stats
        self.state["total_runs"] = self.state.get("total_runs", 0) + 1
        
        # Save state
        self._save_state()
        
        print(f"\n{'='*50}")
        print(f"Sync completed: {datetime.now().isoformat()}")
        print(f"Debtors synced: {total_debtors}")
        print(f"Invoices synced: {total_invoices}")
        print(f"{'='*50}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync WeFact data to Zapier")
    parser.add_argument(
        "--full", 
        action="store_true", 
        help="Perform full sync (all records) instead of incremental"
    )
    parser.add_argument(
        "--full-details",
        action="store_true",
        help="Fetch full debtor details (address, phone, email, etc.) - slower but more complete"
    )
    
    args = parser.parse_args()
    
    sync = WeFactZapierSync()
    sync.sync(full_sync=args.full, full_details=args.full_details)


if __name__ == "__main__":
    main()
