import argparse
import logging
import time
from dotenv import load_dotenv
from fetch_all_transactions import fetch_all_transactions
from csv_writer import write_transactions_to_csv
from utils import is_valid_eth_address

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

def main():
    parser = argparse.ArgumentParser(description="Export categorized ETH transactions to CSV.")
    parser.add_argument("wallet_address", help="Ethereum wallet address")
    parser.add_argument("--output", default="transactions.csv", help="Output CSV file name")
    parser.add_argument("--start-block", type=int, default=0, help="Start block number")
    parser.add_argument("--end-block", type=int, default=99999999, help="End block number")
    args = parser.parse_args()

    if not is_valid_eth_address(args.wallet_address):
        logging.error("Invalid Ethereum wallet address provided.")
        exit(1)

    logging.info(f"Fetching transactions for wallet: {args.wallet_address} (Blocks {args.start_block} → {args.end_block})")

    try:
        start_time = time.time()
        tx_data = fetch_all_transactions(args.wallet_address, start_block=args.start_block, end_block=args.end_block)
        end_time = time.time()
        total_time = end_time - start_time
        logging.info(f"⏱ Total fetch time: {total_time:.2f} seconds")
    except Exception as e:
        logging.error(f"Error while fetching transactions: {e}")
        exit(1)

    if not tx_data:
        logging.info("No transactions found in given block range or API error.")
    else:
        write_transactions_to_csv(tx_data, args.output)
        logging.info(f"Export complete → {args.output}")

if __name__ == "__main__":
    main()
