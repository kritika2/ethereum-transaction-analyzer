import os
import requests
import logging
import re
from urllib.parse import urlencode
from typing import Optional, Dict
import time

# Configure logging (can be customized or moved to main.py)
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

TOKEN_METADATA_CACHE: Dict[str, Dict[str, Optional[int]]] = {}
MAX_RETRIES = 3  # Maximum number of retries for API calls
ETH_ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")  # Compiled regex pattern for Ethereum addresses

def etherscan_request(action: str, address: str, start_block: int = 0, end_block: int = 99999999,
                      page: int = 1, offset: int = 100) -> dict:
    """Makes an API request to Etherscan to fetch transaction or token data."""
    base_url = "https://api.etherscan.io/api"
    api_key = os.getenv("ETHERSCAN_API_KEY")
    params = {
        "module": "account",
        "action": action,
        "address": address,
        "startblock": start_block,
        "endblock": end_block,
        "page": page,
        "offset": offset,
        "sort": "asc",
        "apikey": api_key,
    }
    url = f"{base_url}?{urlencode(params)}"
    logging.debug(f"{action.upper()} | Request URL: {url}")

    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"HTTP error: {response.status_code}")

    data = response.json()
    if data.get("status") != "1":
        logging.debug(f"{action.upper()} | No more data or error.")
        return {"result": []}

    return data

def format_timestamp(ts: Optional[str]) -> str:
    """Convert UNIX timestamp string to human-readable UTC datetime string."""
    if not ts:
        return ""
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(int(ts)))
    except Exception as e:
        logging.warning(f"Failed to format timestamp '{ts}': {e}")
        return ""

def format_wei(value_str: Optional[str], decimals: int = 18) -> str:
    """Format the value from wei or smallest unit to decimal string using decimals."""
    if not value_str or not value_str.isdigit():
        return "0"
    try:
        value_int = int(value_str)
        scaled_value = value_int / (10 ** decimals)
        return str(scaled_value)
    except Exception as e:
        logging.warning(f"Failed to format wei value '{value_str}': {e}")
        return "0"

def calculate_gas_fee(tx: dict) -> str:
    """Calculate gas fee in ETH if fields exist, else return empty string."""
    try:
        gas_used = int(tx.get("gasUsed") or tx.get("gasused") or 0)
        gas_price = int(tx.get("gasPrice") or tx.get("gasprice") or 0)
        fee_eth = (gas_used * gas_price) / 1e18
        return str(fee_eth)
    except Exception as e:
        logging.debug(f"Could not calculate gas fee: {e}")
        return ""

def fetch_token_metadata(contract_address: str) -> dict:
    """Fetch token decimals and symbol for an ERC-20 or ERC-721 token.
    Temporarily using 18 decimals for all tokens. We can extend it in future to use correct decimal by hitting Etherscan API"""
    if not contract_address:
        return {"decimals": 18, "symbol": ""}  # Default for ETH

    if contract_address in TOKEN_METADATA_CACHE:
        return TOKEN_METADATA_CACHE[contract_address]

    TOKEN_METADATA_CACHE[contract_address] = {"decimals": 18, "symbol": ""}
    return TOKEN_METADATA_CACHE[contract_address]

def format_token_amount(value_str: Optional[str], contract_address: str) -> str:
    """Format token value string using token decimals fetched dynamically."""
    if not value_str:
        return "0"
    metadata = fetch_token_metadata(contract_address)
    decimals = metadata.get("decimals", 18)
    return format_wei(value_str, decimals=decimals)

def is_valid_eth_address(address: str) -> bool:
    """Basic Ethereum address validation with compiled regex pattern."""
    if not isinstance(address, str):
        return False
    if not ETH_ADDRESS_PATTERN.fullmatch(address):
        return False
    return True  # Could add checksum validation with eth_utils if desired
