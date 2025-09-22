import pytest
from unittest.mock import patch, MagicMock
from app.utils import (
    is_valid_eth_address, 
    format_timestamp, 
    format_wei, 
    calculate_gas_fee,
    fetch_token_metadata,
    format_token_amount,
    etherscan_request
)


class TestUtils:
    
    def test_is_valid_eth_address_valid(self):
        """Test valid Ethereum addresses"""
        valid_addresses = [
            "0xa39b189482f984388a34460636fea9eb181ad1a6",
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            "0x0000000000000000000000000000000000000000",
            "0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"
        ]
        
        for address in valid_addresses:
            assert is_valid_eth_address(address) is True
    
    def test_is_valid_eth_address_invalid(self):
        """Test invalid Ethereum addresses"""
        invalid_addresses = [
            "0xINVALIDADDRESS1234567890",  # Invalid characters
            "0xa39b189482f984388a34460636fea9eb181ad1a",  # Too short
            "0xa39b189482f984388a34460636fea9eb181ad1a6789",  # Too long
            "a39b189482f984388a34460636fea9eb181ad1a6",  # Missing 0x prefix
            "",  # Empty string
            None,  # None value
            123,  # Non-string type
        ]
        
        for address in invalid_addresses:
            assert is_valid_eth_address(address) is False
    
    def test_format_timestamp_valid(self):
        """Test valid timestamp formatting"""
        # Test that the function returns a properly formatted datetime string
        result = format_timestamp("1631022244")
        assert len(result) == 19  # YYYY-MM-DD HH:MM:SS format
        assert result.startswith("2021-09-07")
        assert ":" in result
        
        # Test zero timestamp
        assert format_timestamp("0") == "1970-01-01 00:00:00"
        
        # Test that it returns a string in the expected format
        result2 = format_timestamp("1672531200")
        assert result2.startswith("2023-01-01")
    
    def test_format_timestamp_invalid(self):
        """Test invalid timestamp handling"""
        invalid_timestamps = [
            "",  # Empty string
            None,  # None value
            "invalid",  # Non-numeric string
            "12.34",  # Float string
        ]
        
        for timestamp in invalid_timestamps:
            assert format_timestamp(timestamp) == ""
    
    def test_format_wei_valid(self):
        """Test valid wei formatting"""
        test_cases = [
            ("1000000000000000000", 18, "1.0"),  # 1 ETH
            ("500000000000000000", 18, "0.5"),   # 0.5 ETH
            ("1000000", 6, "1.0"),                # 1 USDC (6 decimals)
            ("0", 18, "0.0"),                     # Zero value
        ]
        
        for value_str, decimals, expected in test_cases:
            assert format_wei(value_str, decimals) == expected
    
    def test_format_wei_invalid(self):
        """Test invalid wei value handling"""
        invalid_values = [
            "",  # Empty string
            None,  # None value
            "abc",  # Non-numeric string
            "12.34",  # Float string
        ]
        
        for value in invalid_values:
            assert format_wei(value) == "0"
    
    def test_calculate_gas_fee_valid(self):
        """Test valid gas fee calculation"""
        tx = {
            "gasUsed": "21000",
            "gasPrice": "20000000000"  # 20 gwei
        }
        
        result = calculate_gas_fee(tx)
        expected = str((21000 * 20000000000) / 1e18)  # Should be 0.00042 ETH
        
        assert result == expected
    
    def test_calculate_gas_fee_missing_fields(self):
        """Test gas fee calculation with missing fields"""
        test_cases = [
            {},  # Empty transaction
            {"gasUsed": "21000"},  # Missing gasPrice
            {"gasPrice": "20000000000"},  # Missing gasUsed
            {"gasUsed": "", "gasPrice": ""},  # Empty values
        ]
        
        for tx in test_cases:
            result = calculate_gas_fee(tx)
            assert result == "0.0" or result == ""
    
    def test_fetch_token_metadata_caching(self):
        """Test token metadata caching"""
        contract_address = "0x123abc"
        
        # First call should cache the result
        result1 = fetch_token_metadata(contract_address)
        result2 = fetch_token_metadata(contract_address)
        
        # Both results should be identical (cached)
        assert result1 == result2
        assert result1["decimals"] == 18  # Default value
        assert result1["symbol"] == ""    # Default value
    
    def test_fetch_token_metadata_empty_address(self):
        """Test token metadata with empty contract address"""
        result = fetch_token_metadata("")
        
        assert result["decimals"] == 18
        assert result["symbol"] == ""
    
    def test_format_token_amount(self):
        """Test token amount formatting"""
        test_cases = [
            ("1000000000000000000", "0x123", "1.0"),  # Uses default 18 decimals
            ("", "0x123", "0"),                        # Empty value
            (None, "0x123", "0"),                      # None value
        ]
        
        for value_str, contract_address, expected in test_cases:
            result = format_token_amount(value_str, contract_address)
            assert result == expected
    
    @patch('app.utils.requests.get')
    @patch('app.utils.os.getenv')
    def test_etherscan_request_success(self, mock_getenv, mock_get):
        """Test successful Etherscan API request"""
        mock_getenv.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "1",
            "result": [{"hash": "0x123"}]
        }
        mock_get.return_value = mock_response
        
        result = etherscan_request("txlist", "0x123address")
        
        assert result["status"] == "1"
        assert len(result["result"]) == 1
        mock_get.assert_called_once()
    
    @patch('app.utils.requests.get')
    @patch('app.utils.os.getenv')
    def test_etherscan_request_http_error(self, mock_getenv, mock_get):
        """Test Etherscan API request with HTTP error"""
        mock_getenv.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="HTTP error: 500"):
            etherscan_request("txlist", "0x123address")
    
    @patch('app.utils.requests.get')
    @patch('app.utils.os.getenv')
    def test_etherscan_request_api_error(self, mock_getenv, mock_get):
        """Test Etherscan API request with API error response"""
        mock_getenv.return_value = "test_api_key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "0",
            "message": "No transactions found"
        }
        mock_get.return_value = mock_response
        
        result = etherscan_request("txlist", "0x123address")
        
        assert result["result"] == []
