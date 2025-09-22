from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import logging
from typing import List, Dict
from utils import etherscan_request, format_timestamp, format_token_amount, calculate_gas_fee

# --------------------
# Config
# --------------------
RATE_LIMIT = 4  # requests/sec
OFFSET = 100
MAX_TX_PER_RANGE = 10000

# Thread-safe counters for local rate limiting
rate_limit_lock = threading.Lock()
_request_count = 0
_last_reset = time.time()

def rate_limit():
    """Thread-safe local rate limiter."""
    global _request_count, _last_reset
    with rate_limit_lock:
        now = time.time()

        # Reset counter every 1 sec
        if now - _last_reset >= 1:
            _request_count = 0
            _last_reset = now

        _request_count += 1

        # If over limit, wait until reset
        if _request_count > RATE_LIMIT:
            sleep_time = 1 - (now - _last_reset)
            if sleep_time > 0:
                logging.debug(f"Rate limit hit — sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
            _request_count = 1
            _last_reset = time.time()


def fetch_module_transactions(module, tx_type, wallet_address, start_block, end_block):
    local_results = []
    current_start = start_block
    current_end = end_block
    window_size = current_end - current_start

    while current_start <= end_block:
        page = 1
        window_txs = []

        while True:
            rate_limit()  # enforce per-process rate limit

            response = etherscan_request(
                action=module,
                address=wallet_address,
                start_block=current_start,
                end_block=min(current_end, end_block),
                page=page,
                offset=OFFSET,
            )
            result = response.get("result", [])

            if not isinstance(result, list) or not result:
                break

            for tx in result:
                token_id = tx.get("tokenID") or tx.get("tokenId") or ""
                enriched_tx = {
                    "Transaction Hash": tx.get("hash"),
                    "Date & Time": format_timestamp(tx.get("timeStamp")),
                    "From Address": tx.get("from"),
                    "To Address": tx.get("to"),
                    "Transaction Type": tx_type,
                    "Asset Contract Address": tx.get("contractAddress", ""),
                    "Asset Symbol / Name": tx.get("tokenSymbol") or ("ETH" if tx_type == "External (Normal) Transfer" else ""),
                    "Token ID": token_id,
                    "Value / Amount": format_token_amount(tx.get("value"), tx.get("contractAddress", "")),
                    "Gas Fee (ETH)": calculate_gas_fee(tx),
                }
                local_results.append(enriched_tx)
                window_txs.append(enriched_tx)

            if len(result) < OFFSET:
                break
            page += 1

        # Adaptive window size
        tx_count = len(window_txs)
        if tx_count >= MAX_TX_PER_RANGE:
            window_size = max(1, window_size // 2)
            logging.info(f"High density — shrinking block window to {window_size}")
            current_end = current_start + window_size
            continue
        else:
            current_start = current_end + 1
            window_size = min(window_size * 2, end_block - current_start + 1)
            current_end = current_start + window_size

    return local_results


def fetch_all_transactions(wallet_address: str, start_block: int, end_block: int) -> List[Dict]:
    modules = [
        ("txlist", "External (Normal) Transfer"),
        ("txlistinternal", "Internal Transfer"),
        ("tokentx", "ERC-20"),
        ("tokennfttx", "ERC-721"),
    ]

    results = []
    with ThreadPoolExecutor(max_workers=len(modules)) as executor:
        futures = {
            executor.submit(fetch_module_transactions, m, t, wallet_address, start_block, end_block): t
            for m, t in modules
        }
        for future in as_completed(futures):
            try:
                results.extend(future.result())
            except Exception as e:
                logging.error(f"Error fetching {futures[future]}: {e}")

    return results
