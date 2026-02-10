#!/usr/bin/env python3
"""
Push a single WeFact record to Zapier by ID
Usage: python push_single.py --type debtor --id 1
       python push_single.py --type invoice --id 707
"""

import argparse
import requests
from datetime import datetime

WEFACT_API_URL = "https://api.mijnwefact.nl/v2/"
WEFACT_API_KEY = "309db38a9ca280c54bfcfdec4540f28d"

ZAPIER_WEBHOOKS = {
    "debtor": "https://hooks.zapier.com/hooks/catch/18377081/uei7n5h/",
    "invoice": "https://hooks.zapier.com/hooks/catch/18377081/uei7kn7/"
}


def fetch_single(controller: str, identifier: str):
    """Fetch a single record from WeFact."""
    payload = {
        "api_key": WEFACT_API_KEY,
        "controller": controller,
        "action": "show",
        "Identifier": identifier
    }
    
    response = requests.post(WEFACT_API_URL, json=payload)
    response.raise_for_status()
    return response.json()


def push_to_zapier(data_type: str, record: dict):
    """Push record to Zapier."""
    webhook_url = ZAPIER_WEBHOOKS.get(data_type)
    
    payload = {
        "data_type": data_type + "s",
        "sync_time": datetime.now().isoformat(),
        "record": record
    }
    
    response = requests.post(webhook_url, json=payload)
    response.raise_for_status()
    return response


def main():
    parser = argparse.ArgumentParser(description="Push single WeFact record to Zapier")
    parser.add_argument("--type", choices=["debtor", "invoice"], required=True,
                        help="Type of record: debtor or invoice")
    parser.add_argument("--id", required=True,
                        help="Record Identifier (e.g., 1, 707)")
    
    args = parser.parse_args()
    
    print(f"Fetching {args.type} {args.id}...")
    
    try:
        # Fetch from WeFact
        result = fetch_single(args.type, args.id)
        record_key = args.type  # 'debtor' or 'invoice'
        
        if record_key not in result:
            print(f"Error: {args.type} {args.id} not found")
            print(f"Response: {result}")
            return
        
        record = result[record_key]
        
        # Push to Zapier
        print(f"Pushing to Zapier...")
        response = push_to_zapier(args.type, record)
        
        print(f"✅ Success! {args.type.title()} {args.id} sent to Zapier")
        print(f"   Status: {response.status_code}")
        
        # Show what was sent
        if args.type == "debtor":
            name = record.get('CompanyName') or f"{record.get('Initials', '')} {record.get('SurName', '')}".strip()
            print(f"   Name: {name}")
            print(f"   Email: {record.get('EmailAddress', 'N/A')}")
        else:
            print(f"   Invoice: {record.get('InvoiceCode')}")
            print(f"   Amount: €{record.get('AmountIncl')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
