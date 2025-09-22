import csv
import logging
from typing import List, Dict

def deduplicate_transactions(transactions: List[Dict]) -> List[Dict]:
    """Remove duplicate transactions based on (hash, type, token_id) key."""
    seen = set()
    unique_txs = []
    for tx in transactions:
        # Skip invalid transactions that aren't dictionaries
        if not isinstance(tx, dict):
            continue
        try:
            key = (tx["Transaction Hash"], tx["Transaction Type"], tx.get("Token ID", ""))
            if key not in seen:
                seen.add(key)
                unique_txs.append(tx)
        except KeyError:
            # Skip transactions missing required fields
            logging.warning(f"Skipping transaction with missing required fields: {tx}")
            continue
    return unique_txs

def write_transactions_to_csv(transactions: List[Dict], output_file: str) -> None:
    """Write list of transaction dicts to CSV file."""
    fieldnames = [
        "Transaction Hash",
        "Date & Time",
        "From Address",
        "To Address",
        "Transaction Type",
        "Asset Contract Address",
        "Asset Symbol / Name",
        "Token ID",
        "Value / Amount",
        "Gas Fee (ETH)",
    ]

    transactions = deduplicate_transactions(transactions)

    with open(output_file, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for tx in transactions:
            if isinstance(tx, dict):
                writer.writerow({key: tx.get(key, "") for key in fieldnames})
            else:
                logging.warning(f"Skipped non-dictionary entry: {tx}")
