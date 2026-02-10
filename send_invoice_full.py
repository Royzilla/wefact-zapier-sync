#!/usr/bin/env python3
"""
Send full invoice details to Zapier with line items formatted as:
Number | ProductCode | Description (each on separate lines)
"""

import argparse
import requests
import json
from datetime import datetime

WEFACT_API_URL = "https://api.mijnwefact.nl/v2/"
WEFACT_API_KEY = "309db38a9ca280c54bfcfdec4540f28d"
ZAPIER_WEBHOOK = "https://hooks.zapier.com/hooks/catch/18377081/uei7kn7/"


def fetch_invoice(identifier: str):
    """Fetch full invoice details from WeFact."""
    payload = {
        "api_key": WEFACT_API_KEY,
        "controller": "invoice",
        "action": "show",
        "Identifier": identifier
    }
    response = requests.post(WEFACT_API_URL, json=payload)
    response.raise_for_status()
    return response.json().get("invoice", {})


def format_line_items(lines):
    """Format line items as list with Number, ProductCode, Description."""
    formatted = []
    for line in lines:
        formatted.append({
            "Number": line.get("Number", ""),
            "ProductCode": line.get("ProductCode", ""),
            "Description": line.get("Description", "")
        })
    return formatted


def send_invoice(invoice_id: str):
    """Send full invoice with formatted line items."""
    print(f"Fetching invoice {invoice_id}...")
    invoice = fetch_invoice(invoice_id)
    
    if not invoice:
        print(f"❌ Invoice {invoice_id} not found")
        return
    
    # Build payload with full invoice details
    payload = {
        "invoice_code": invoice.get("InvoiceCode"),
        "invoice_date": invoice.get("Date"),
        "debtor_code": invoice.get("DebtorCode"),
        "debtor_name": f"{invoice.get('Initials', '')} {invoice.get('SurName', '')}".strip() or invoice.get("CompanyName", ""),
        "debtor_email": invoice.get("EmailAddress"),
        "amount_excl": invoice.get("AmountExcl"),
        "amount_incl": invoice.get("AmountIncl"),
        "amount_outstanding": invoice.get("AmountOutstanding"),
        "status": invoice.get("Status"),
        "line_items": format_line_items(invoice.get("InvoiceLines", [])),
        "sync_time": datetime.now().isoformat()
    }
    
    # Send to Zapier
    print(f"Sending invoice {payload['invoice_code']} with {len(payload['line_items'])} line items...")
    response = requests.post(ZAPIER_WEBHOOK, json=payload)
    
    if response.status_code == 200:
        print(f"✅ Success!")
        print(f"\nInvoice: {payload['invoice_code']}")
        print(f"Customer: {payload['debtor_name']}")
        print(f"Amount: €{payload['amount_incl']}")
        print(f"\nLine Items:")
        for item in payload['line_items']:
            print(f"  {item['Number']:>3} | {item['ProductCode']:<15} | {item['Description'][:50]}")
    else:
        print(f"❌ Failed: {response.status_code}")


def main():
    parser = argparse.ArgumentParser(description="Send full invoice details to Zapier")
    parser.add_argument("--id", required=True, help="Invoice Identifier (e.g., 707)")
    
    args = parser.parse_args()
    
    try:
        send_invoice(args.id)
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
