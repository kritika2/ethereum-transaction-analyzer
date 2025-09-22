import pytest
import csv
import os
import tempfile
from app.csv_writer import write_transactions_to_csv, deduplicate_transactions


class TestCsvWriter:
    
    def test_deduplicate_transactions(self):
        """Test transaction deduplication logic"""
        transactions = [
            {
                "Transaction Hash": "0x123",
                "Transaction Type": "External",
                "Token ID": "",
                "Value / Amount": "1.0"
            },
            {
                "Transaction Hash": "0x123",
                "Transaction Type": "External", 
                "Token ID": "",
                "Value / Amount": "1.0"
            },  # Duplicate
            {
                "Transaction Hash": "0x456",
                "Transaction Type": "ERC-20",
                "Token ID": "123",
                "Value / Amount": "2.0"
            }
        ]
        
        result = deduplicate_transactions(transactions)
        
        assert len(result) == 2
        assert result[0]["Transaction Hash"] == "0x123"
        assert result[1]["Transaction Hash"] == "0x456"

    def test_deduplicate_different_token_ids(self):
        """Test that transactions with same hash but different token IDs are kept"""
        transactions = [
            {
                "Transaction Hash": "0x123",
                "Transaction Type": "ERC-721",
                "Token ID": "1",
                "Value / Amount": "1"
            },
            {
                "Transaction Hash": "0x123",
                "Transaction Type": "ERC-721",
                "Token ID": "2", 
                "Value / Amount": "1"
            }
        ]
        
        result = deduplicate_transactions(transactions)
        
        assert len(result) == 2  # Should keep both due to different token IDs

    def test_write_transactions_to_csv_success(self):
        """Test successful CSV writing"""
        transactions = [
            {
                "Transaction Hash": "0x123abc",
                "Date & Time": "2021-09-07 17:04:04",
                "From Address": "0xfrom123",
                "To Address": "0xto456",
                "Transaction Type": "External (Normal) Transfer",
                "Asset Contract Address": "",
                "Asset Symbol / Name": "ETH",
                "Token ID": "",
                "Value / Amount": "1.0",
                "Gas Fee (ETH)": "0.00042"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            write_transactions_to_csv(transactions, tmp_filename)
            
            # Verify file was created and has correct content
            assert os.path.exists(tmp_filename)
            
            with open(tmp_filename, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                assert len(rows) == 1
                assert rows[0]["Transaction Hash"] == "0x123abc"
                assert rows[0]["Transaction Type"] == "External (Normal) Transfer"
                assert rows[0]["Value / Amount"] == "1.0"
        
        finally:
            # Clean up temp file
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

    def test_write_transactions_empty_list(self):
        """Test writing empty transaction list"""
        transactions = []
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            write_transactions_to_csv(transactions, tmp_filename)
            
            # Verify file was created with only headers
            assert os.path.exists(tmp_filename)
            
            with open(tmp_filename, 'r') as csvfile:
                reader = csv.reader(csvfile)
                rows = list(reader)
                
                assert len(rows) == 1  # Only header row
                assert "Transaction Hash" in rows[0]
        
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

    def test_write_transactions_missing_fields(self):
        """Test CSV writing with transactions missing some fields"""
        transactions = [
            {
                "Transaction Hash": "0x123",
                "Transaction Type": "External",
                # Missing other fields
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            write_transactions_to_csv(transactions, tmp_filename)
            
            with open(tmp_filename, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                assert len(rows) == 1
                assert rows[0]["Transaction Hash"] == "0x123"
                assert rows[0]["Date & Time"] == ""  # Should default to empty string
        
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

    def test_write_transactions_invalid_data_handling(self):
        """Test handling of invalid transaction data"""
        transactions = [
            "invalid_transaction",  # String instead of dict
            {
                "Transaction Hash": "0x123",
                "Transaction Type": "External"
            }  # Valid transaction
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            write_transactions_to_csv(transactions, tmp_filename)
            
            with open(tmp_filename, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
                # Should only process valid transactions
                assert len(rows) == 1
                assert rows[0]["Transaction Hash"] == "0x123"
        
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

    def test_csv_fieldnames_order(self):
        """Test that CSV fieldnames are in the correct order"""
        transactions = [
            {
                "Transaction Hash": "0x123",
                "Date & Time": "2021-09-07 17:04:04",
                "From Address": "0xfrom",
                "To Address": "0xto",
                "Transaction Type": "External",
                "Asset Contract Address": "",
                "Asset Symbol / Name": "ETH",
                "Token ID": "",
                "Value / Amount": "1.0",
                "Gas Fee (ETH)": "0.001"
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            write_transactions_to_csv(transactions, tmp_filename)
            
            with open(tmp_filename, 'r') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                
                expected_order = [
                    "Transaction Hash",
                    "Date & Time", 
                    "From Address",
                    "To Address",
                    "Transaction Type",
                    "Asset Contract Address",
                    "Asset Symbol / Name",
                    "Token ID",
                    "Value / Amount",
                    "Gas Fee (ETH)"
                ]
                
                assert header == expected_order
        
        finally:
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
