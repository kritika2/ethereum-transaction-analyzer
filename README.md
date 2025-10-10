# 🚀 Ethereum Transaction Analyzer

This project fetches Ethereum transaction data for a specified wallet and exports it to a CSV file. The data includes details for different types of transactions: External, Internal, ERC-20, and ERC-721.

> *"Turning blockchain chaos into beautiful CSV order, one transaction at a time!"* 📊💎

## Objective

- Retrieve and categorize transactions into different types.
- Export the data to a formatted CSV file.


             +---------------------------+
             | Ethereum Wallet Address   |
             +---------------------------+
                         |
                         v
             +---------------------------+
             |      Fetcher Layer        | <-- Etherscan APIs:
             |  - External Transactions  |     - txlist
             |  - Internal Transactions  |     - txlistinternal
             |  - ERC-20 & ERC-721 Txns  |     - tokentx, tokennfttx
             +---------------------------+
                         |
                         v
             +---------------------------+
             |  In-Memory Processing     |
             |  - Normalize fields       |
             |  - Categorize types       |
             |  - Gas/Value extraction   |
             +---------------------------+
                         |
                         v
             +---------------------------+
             |       CSV Exporter        |
             |  - pandas to_csv()        |
             +---------------------------+
                         |
                         v
             +---------------------------+
             |       Output CSV File     |
             +---------------------------+


## Assumptions

### Data & API Assumptions
- **Etherscan API Reliability:** The Etherscan API is available and returns consistent data structures for all transaction types.
- **Token Decimals:** All ERC-20 tokens use 18 decimals (temporary simplification - can be enhanced to fetch actual decimals via contract calls).
- **Block Range Logic:** Block range endpoints are inclusive, and the default end block (99999999) represents "latest" for practical purposes.
- **Transaction Uniqueness:** Duplicate transactions are identified by the combination of transaction hash, transaction type, and token ID.
- **Rate Limiting:** The Etherscan API has reasonable rate limits that can be handled with basic retry logic and delays.

### Business Logic Assumptions
- **Gas Fee Calculation:** Gas fees are only relevant for normal/internal transactions that have gasUsed and gasPrice fields.
- **Address Validation:** Basic Ethereum address format validation (0x + 40 hex chars) is sufficient for the use case.
- **Transaction Types:** Four main transaction types cover the scope: External, Internal, ERC-20, and ERC-721.

## Architecture Decisions

### Design Patterns
- **Separation of Concerns:** Each module handles a single responsibility:
  - `main.py`: CLI interface and orchestration
  - `fetch_all_transactions.py`: API data retrieval with retry logic
  - `csv_writer.py`: Data formatting and CSV export
  - `utils.py`: Shared utilities and helper functions

### Error Handling & Resilience
- **Exponential Backoff:** Implements retry logic with exponential backoff (1s → 2s → 4s → 8s → 16s max) to handle API rate limits gracefully.
- **Pagination Safety:** Limits maximum pages per transaction type (50) to prevent infinite loops from API inconsistencies.
- **Graceful Degradation:** Continues processing other transaction types even if one type fails after max retries.

### Performance Optimizations
- **In-Memory Caching:** Token metadata is cached in memory to avoid redundant API calls for the same contract addresses.
- **Batch Processing:** Fetches 100 transactions per API call (Etherscan's max offset) to minimize HTTP requests.
- **Request Throttling:** 200ms delay between API calls to respect rate limits and avoid being blocked.

### Data Processing
- **Deduplication Strategy:** Uses a set-based approach with composite keys (hash + type + tokenId) for O(1) duplicate detection.
- **Flexible CSV Schema:** Standardized column names that accommodate all transaction types while leaving empty fields for irrelevant data.
- **Timestamp Normalization:** Converts Unix timestamps to human-readable UTC format for better CSV readability.

### Security & Configuration
- **Environment Variables:** API keys are loaded from `.env` files to keep sensitive data out of source code.
- **Input Validation:** Validates Ethereum addresses using regex patterns before making API calls.
- **Logging:** Comprehensive logging at INFO level for monitoring, with DEBUG level for detailed troubleshooting.

## Setup

### Prerequisites
- Python 3.7+ installed on your system
- Etherscan API key (free from https://etherscan.io/apis)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/kritika2/ethereum-transaction-analyzer.git
   cd ethereum-transaction-analyzer
   ```

2. **Set up the virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file in the root directory:
   ```bash
   echo "ETHERSCAN_API_KEY=your_api_key_here" > .env
   ```
   Replace `your_api_key_here` with your actual Etherscan API key.

## Running the Script

```bash

"python3 main.py <your_wallet_address> --start-block 18140000 --end-block 18140100 --output sample_transactions.csv


python3 main.py <your_wallet_address> --start-block 0 --end-block 99999999 --output all_transactions.csv

The number 99999999 is not the real block height limit. It's simply an arbitrarily large number that's higher than the current Ethereum block number.
As of August 2025, the Ethereum chain is around block 20,900,000.


sample:
python3 app/main.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --start-block 17140000 --end-block 19140100 --output report.csv
python3 app/main.py 0x6b8c4eC3B0C29AA9F8758787B37c7B35d92c53d6 --start-block 17140000 --end-block 19140100 --output report.csv"

```

## Testing

### Run all tests
Activate the virtual environment and run:
```bash
source venv/bin/activate && pytest tests/
```

### Run tests with verbose output
```bash
source venv/bin/activate && pytest tests/ -v
```

### Run specific test files
```bash
source venv/bin/activate && pytest tests/test_csv_writer.py tests/test_utils.py -v
```

### Run a specific test
```bash
source venv/bin/activate && pytest tests/test_utils.py::TestUtils::test_is_valid_eth_address_valid -v
```

### Run tests with coverage
Install coverage package if needed and then run:
```bash
source venv/bin/activate && pytest tests/ --cov=app
```

## Future Enhancements

These can be done in future as enhancement, but not part of the current implementation:

### Scalability & Data Architecture
**Database Integration**:
- When scaling, data will come from upstream sources and UI interactions
- Implement paginated data handling for large datasets
- Store all transaction details in a database (PostgreSQL/MongoDB) for persistent storage
- Fetch data from database instead of making repeated API calls
- Implement caching layers (Redis/Memcached) for frequently accessed data

**API Limitations & Enhancements**:
- **Etherscan 10K Limit**: Etherscan limits responses to 10,000 results per request. For wallets with >10K transactions, implement manual pagination using startblock and endblock parameters
- **Enhanced Retry Logic**: Add specific retry logic for 429 Too Many Requests responses with exponential backoff
- **Adaptive Block Windows**: Make block_window adaptive based on transaction density - use smaller windows for high-activity periods and larger windows for sparse activity
- **Block Caching**: Cache latest_block and use it as max_blocks to avoid unnecessary API calls and improve efficiency
- **Dynamic Token Decimals**: ERC-20 tokens may have varying decimals (commonly 6 to 18). To display accurate token amounts, enhance the system to dynamically fetch token metadata (decimals and symbol) from the Etherscan API and cache it during runtime. If metadata is unavailable, default to 18 decimals (consistent with ETH). This ensures correct human-readable token amounts in the CSV output. Currently, our code defaults all tokens to 18 decimals.
- **Enhanced Gas Fee Attribution**: Gas fees are computed from the gasUsed and gasPrice fields of transactions. For token transfers and internal transactions where this info is often unavailable, the gas fee field may be empty or zero. Accurate gas fee attribution in complex transactions requires correlating parent transactions, which is a planned enhancement to provide more precise cost tracking.

### CI/CD, Robustness, and Security

**CI/CD**:
- Setup GitHub Actions to run tests and linting on every pull request.

**Robustness**:
- Implement thorough exception handling and logging to detect and handle edge cases.

**Scalability**:
- Consider refactoring to microservices for more extensive use cases, ensuring independent scaling of components.
- Implement API rate limiting and queue-based processing for high-volume requests.

**Security**:
- Ensure sensitive information, like API keys, is stored securely using environment variables or vault systems.

---

## 👋 About This Project

```
⛓️⛓️⛓️ BLOCKCHAIN TRANSACTION DETECTIVE ⛓️⛓️⛓️

"Every transaction tells a story...
This tool just makes sure it's properly formatted in CSV!"

🔍 Investigates: ETH, ERC-20, ERC-721, Internal transfers
📊 Exports: Clean, deduplicated CSV reports
🚀 Speed: Batch processing with retry logic
⚙️ Quality: Comprehensive test coverage

          Built with ❤️ for blockchain enthusiasts
      "Making crypto accounting less cryptic!"
```

*P.S. - No transactions were harmed in the making of this CSV exporter. All gas fees were calculated responsibly.* 🌱⛽



Interface -> call api
etherscan1
blockchain1 -> 