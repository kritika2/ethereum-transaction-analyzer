import time
import random
import logging
from typing import List, Dict
from utils import etherscan_request, format_timestamp, format_token_amount, calculate_gas_fee

MAX_PAGES_PER_TYPE = 50  # max pages per tx type to avoid infinite loop
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 16.0


def fetch_all_transactions(wallet_address: str, start_block: int, end_block: int) -> List[Dict]:
    """Fetch all transactions for wallet address categorized by type, with retry and pagination."""
    all_transactions = []

    # Etherscan API endpoints for different transaction types
    modules = [
        ("txlist", "External (Normal) Transfer"),
        ("txlistinternal", "Internal Transfer"),
        ("tokentx", "ERC-20"),
        ("tokennfttx", "ERC-721"),
    ]

    for module, tx_type in modules:
        logging.info(f"Fetching {tx_type} transactions...")
        page = 1
        retry_count = 0
        backoff = INITIAL_BACKOFF

        while page <= MAX_PAGES_PER_TYPE:
            try:
                response = etherscan_request(
                    action=module,
                    address=wallet_address,
                    start_block=start_block,
                    end_block=end_block,
                    page=page,
                    offset=100,
                )
                result = response.get("result", [])

                if not isinstance(result, list) or not result:
                    logging.info(f"{tx_type}: No more data at page {page}.")
                    break

                for tx in result:
                    if not isinstance(tx, dict):
                        logging.warning(f"Skipping invalid transaction: {tx}")
                        continue

                    token_id = tx.get("tokenID") or tx.get("tokenId") or ""

                    enriched_tx = {
                        "Transaction Hash": tx.get("hash"),
                        "Date & Time": format_timestamp(tx.get("timeStamp")),
                        "From Address": tx.get("from"),
                        "To Address": tx.get("to"),
                        "Transaction Type": tx_type,
                        "Asset Contract Address": tx.get("contractAddress", ""),
                        "Asset Symbol / Name": tx.get("tokenSymbol") or (
                            "ETH" if tx_type == "External (Normal) Transfer" else ""),
                        "Token ID": token_id,
                        "Value / Amount": format_token_amount(tx.get("value"), tx.get("contractAddress", "")),
                        "Gas Fee (ETH)": calculate_gas_fee(tx),
                    }

                    all_transactions.append(enriched_tx)

                page += 1
                retry_count = 0
                backoff = INITIAL_BACKOFF
                time.sleep(0.2)

            except Exception as e:
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    logging.error(f"Max retries reached for {tx_type} page {page}: {e}")
                    break
                else:
                    sleep_time = backoff + random.uniform(0, 0.5)
                    logging.warning(
                        f"Error fetching {tx_type} page {page}, retry {retry_count}/{MAX_RETRIES} after {sleep_time:.1f}s: {e}")
                    time.sleep(sleep_time)
                    backoff = min(backoff * 2, MAX_BACKOFF)

    return all_transactions
