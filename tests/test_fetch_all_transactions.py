import pytest
from unittest.mock import patch, MagicMock
from app.fetch_all_transactions import fetch_all_transactions


class TestFetchAllTransactions:
    
    @patch('app.fetch_all_transactions.etherscan_request')
    def test_fetch_transactions_success(self, mock_request):
        """Test successful transaction fetching"""
        mock_request.return_value = {
            "result": [
                {
                    "hash": "0x123abc",
                    "timeStamp": "1631022244",
                    "from": "0xfrom123",
                    "to": "0xto456",
                    "value": "1000000000000000000",
                    "gasUsed": "21000",
                    "gasPrice": "20000000000"
                }
            ]
        }
        
        result = fetch_all_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6", 0, 100)
        
        # Should have transactions from all 4 types (each type returns 1 transaction per page until empty)
        assert len(result) > 0
        assert mock_request.call_count >= 4  # At least one call per transaction type

    @patch('app.fetch_all_transactions.etherscan_request')
    def test_fetch_transactions_empty_result(self, mock_request):
        """Test handling of empty API results"""
        mock_request.return_value = {"result": []}
        
        result = fetch_all_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6", 0, 100)
        
        assert result == []

    @patch('app.fetch_all_transactions.etherscan_request')
    def test_fetch_transactions_with_pagination(self, mock_request):
        """Test pagination handling"""
        # First call returns 100 transactions, second call returns empty
        mock_request.side_effect = [
            {"result": [{"hash": f"0x{i}", "timeStamp": "1631022244", "from": "0xfrom", "to": "0xto", "value": "1000"} for i in range(100)]},
            {"result": []}
        ]
        
        result = fetch_all_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6", 0, 100)
        
        # Should have made multiple calls for pagination
        assert mock_request.call_count >= 4  # At least one call per transaction type

    @patch('app.fetch_all_transactions.etherscan_request')
    @patch('app.fetch_all_transactions.time.sleep')
    def test_fetch_transactions_retry_logic(self, mock_sleep, mock_request):
        """Test retry logic on API failures"""
        # First call fails, second succeeds
        mock_request.side_effect = [
            Exception("API Error"),
            {"result": []}
        ]
        
        result = fetch_all_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6", 0, 100)
        
        # Should have retried and eventually succeeded
        assert mock_sleep.called
        assert result == []

    @patch('app.fetch_all_transactions.etherscan_request')
    def test_fetch_transactions_max_retries_exceeded(self, mock_request):
        """Test behavior when max retries are exceeded"""
        mock_request.side_effect = Exception("Persistent API Error")
        
        result = fetch_all_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6", 0, 100)
        
        # Should return empty list after max retries
        assert result == []

    @patch('app.fetch_all_transactions.etherscan_request')
    def test_fetch_transactions_invalid_data_handling(self, mock_request):
        """Test handling of invalid transaction data"""
        mock_request.return_value = {
            "result": [
                "invalid_transaction",  # String instead of dict
                {"hash": "0x123"},  # Missing required fields
                {
                    "hash": "0x456",
                    "timeStamp": "1631022244",
                    "from": "0xfrom",
                    "to": "0xto",
                    "value": "1000"
                }  # Valid transaction
            ]
        }
        
        result = fetch_all_transactions("0xa39b189482f984388a34460636fea9eb181ad1a6", 0, 100)
        
        # Should handle invalid data gracefully
        assert len(result) > 0  # Should still process valid transactions
