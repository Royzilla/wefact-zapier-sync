#!/usr/bin/env python3
"""
Push invoice line items to Zapier as raw JSON array
Format: [{"Aantal":"1","ProductCode":"LP02","Omschrijving":"..."}]
Usage: python push_invoice_lines.py --id 707
"""

import argparse
import requests
import json
from datetime import datetime

WEFACT_API_URL = "https://api.mijnwefact.nl/v2/"
WEFACT_API_KEY = "309db38a9ca280c54bfcfdec4540f28d"
ZAPIER_WEBHOOK = "https://hooks.zapier.com/hooks/catch/18377081/uei7kn7/"


def fetch_invoice(identifier: str):
    """Fetch invoice from WeFact."""
    payload = {
        "api_key": WEFACT_API_KEY,
        "controller": "invoice",
        "action": "show",
        "Identifier": identifier
    }
    response = requests.post(WEFACT_API_URL, json=payload)
    response.raise_for_status()
    return response.json().get("invoice", {})


def push_line_items(invoice_id: str):
    """Push invoice line items as raw JSON array."""
    print(f"Fetching invoice {invoice_id}...")
    invoice = fetch_invoice(invoice_id)
    
    if not invoice:
        print(f"❌ Invoice {invoice_id} not found")
        return
    
    lines = invoice.get("InvoiceLines", [])
    print(f"Found {len(lines)} line items")
    print(f"Sending each line to Zapier separately...\n")
    
    success_count = 0
    for line in lines:
        # Build payload for single line
        payload = {
            "invoicerules": {
                "Aantal": line.get("Number", ""),
                "ProductCode": line.get("ProductCode", ""),
                "Omschrijving": line.get("Description", "")
            }
        }
        
        # Send to Zapier
        print(f"Sending: Aantal={line.get('Number')}, ProductCode={line.get('ProductCode')}")
        response = requests.post(ZAPIER_WEBHOOK, json=payload)
        
        if response.status_code == 200:
            success_count += 1
            print(f"✅ Sent successfully")
        else:
            print(f"❌ Failed: {response.status_code}")
    
    print(f"\n🎉 Done! Sent {success_count}/{len(lines)} line items")


def main():
    parser = argparse.ArgumentParser(description="Push invoice line items to Zapier")
    parser.add_argument("--id", required=True, help="Invoice Identifier (e.g., 707)")
    
    args = parser.parse_args()
    
    try:
        push_line_items(args.id)
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
