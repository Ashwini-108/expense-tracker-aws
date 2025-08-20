"""
Tests for the Expense Tracker application
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the src directory to the Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from expense_tracker import ExpenseTracker
from aws_client import AWSClient


class TestAWSClient:
    """Test AWS Client functionality"""
    
    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-east-1',
        'S3_BUCKET_NAME': 'expense-tracker-ashwini-4',
        'CLOUDWATCH_LOG_GROUP': 'test-logs'
    })
    def test_aws_client_init_success(self, mock_boto3):
        """Test successful AWS client initialization"""
        # Mock the clients
        mock_s3 = Mock()
        mock_cloudwatch = Mock()
        mock_boto3.side_effect = [mock_s3, mock_cloudwatch]
        
        # Mock CloudWatch log group creation
        mock_cloudwatch.create_log_group.side_effect = Exception("ResourceAlreadyExistsException")
        
        client = AWSClient()
        
        assert client.s3_bucket == 'expense-tracker-ashwini-4'
        assert client.aws_region == 'us-east-1'
        assert client.log_group == 'test-logs'
    
    @patch.dict(os.environ, {})
    def test_aws_client_missing_bucket_name(self):
        """Test AWS client fails without bucket name"""
        with pytest.raises(Exception) as exc_info:
            AWSClient()
        assert "S3_BUCKET_NAME environment variable is required" in str(exc_info.value)
    
    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-east-1',
        'S3_BUCKET_NAME': 'expense-tracker-ashwini-4',
        'CLOUDWATCH_LOG_GROUP': 'test-logs'
    })
    def test_upload_expenses_success(self, mock_boto3):
        """Test successful expense upload to S3"""
        # Mock the clients
        mock_s3 = Mock()
        mock_cloudwatch = Mock()
        mock_boto3.side_effect = [mock_s3, mock_cloudwatch]
        mock_cloudwatch.create_log_group.side_effect = Exception("ResourceAlreadyExistsException")
        
        client = AWSClient()
        
        # Mock successful upload
        mock_s3.put_object.return_value = True
        
        # Test data
        expenses = [
            {'id': 1, 'description': 'Test', 'amount': 10.0, 'category': 'Test'}
        ]
        
        result = client.upload_expenses_to_s3(expenses, 'test_user')
        
        assert result is True
        mock_s3.put_object.assert_called_once()
    
    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-east-1',
        'S3_BUCKET_NAME': 'expense-tracker-ashwini-4',
        'CLOUDWATCH_LOG_GROUP': 'test-logs'
    })
    def test_download_expenses_success(self, mock_boto3):
        """Test successful expense download from S3"""
        # Mock the clients
        mock_s3 = Mock()
        mock_cloudwatch = Mock()
        mock_boto3.side_effect = [mock_s3, mock_cloudwatch]
        mock_cloudwatch.create_log_group.side_effect = Exception("ResourceAlreadyExistsException")
        
        client = AWSClient()
        
        # Mock successful download
        mock_response = {
            'Body': Mock()
        }
        test_data = '[{"id": 1, "description": "Test", "amount": 10.0}]'
        mock_response['Body'].read.return_value = test_data.encode('utf-8')
        mock_s3.get_object.return_value = mock_response
        
        result = client.download_expenses_from_s3('test_user')
        
        assert len(result) == 1
        assert result[0]['description'] == 'Test'
    
    @patch('boto3.client')
    @patch.dict(os.environ, {
        'AWS_REGION': 'us-east-1',
        'S3_BUCKET_NAME': 'expense-tracker-ashwini-4',
        'CLOUDWATCH_LOG_GROUP': 'test-logs'
    })
    def test_download_expenses_no_file(self, mock_boto3):
        """Test download when no file exists"""
        from botocore.exceptions import ClientError
        
        # Mock the clients
        mock_s3 = Mock()
        mock_cloudwatch = Mock()
        mock_boto3.side_effect = [mock_s3, mock_cloudwatch]
        mock_cloudwatch.create_log_group.side_effect = Exception("ResourceAlreadyExistsException")
        
        client = AWSClient()
        
        # Mock no file found
        error_response = {'Error': {'Code': 'NoSuchKey'}}
        mock_s3.get_object.side_effect = ClientError(error_response, 'GetObject')
        
        result = client.download_expenses_from_s3('test_user')
        
        assert result == []


class TestExpenseTracker:
    """Test Expense Tracker functionality"""
    
    @patch('src.expense_tracker.AWSClient')
    @patch('src.expense_tracker.load_dotenv')
    def test_expense_tracker_init_success(self, mock_load_dotenv, mock_aws_client):
        """Test successful ExpenseTracker initialization"""
        # Mock AWS client
        mock_client_instance = Mock()
        mock_client_instance.download_expenses_from_s3.return_value = []
        mock_aws_client.return_value = mock_client_instance
        
        tracker = ExpenseTracker()
        
        assert tracker.user_id == "default"
        assert tracker.expenses == []
        mock_load_dotenv.assert_called_once()
    
    @patch('src.expense_tracker.AWSClient')
    @patch('src.expense_tracker.load_dotenv')
    def test_add_expense_success(self, mock_load_dotenv, mock_aws_client):
        """Test adding expense successfully"""
        # Mock AWS client
        mock_client_instance = Mock()
        mock_client_instance.download_expenses_from_s3.return_value = []
        mock_client_instance.upload_expenses_to_s3.return_value = True
        mock_aws_client.return_value = mock_client_instance
        
        tracker = ExpenseTracker()
        
        result = tracker.add_expense("Coffee", 4.50, "Food")
        
        assert result is True
        assert len(tracker.expenses) == 1
        assert tracker.expenses[0]['description'] == "Coffee"
        assert tracker.expenses[0]['amount'] == 4.50
        assert tracker.expenses[0]['category'] == "Food"
        mock_client_instance.upload_expenses_to_s3.assert_called_once()
    
    @patch('src.expense_tracker.AWSClient')
    @patch('src.expense_tracker.load_dotenv')
    def test_add_expense_invalid_amount(self, mock_load_dotenv, mock_aws_client):
        """Test adding expense with invalid amount"""
        # Mock AWS client
        mock_client_instance = Mock()
        mock_client_instance.download_expenses_from_s3.return_value = []
        mock_aws_client.return_value = mock_client_instance
        
        tracker = ExpenseTracker()
        
        result = tracker.add_expense("Coffee", -5.0, "Food")
        
        assert result is False
        assert len(tracker.expenses) == 0
    
    @patch('src.expense_tracker.AWSClient')
    @patch('src.expense_tracker.load_dotenv')
    def test_add_expense_empty_description(self, mock_load_dotenv, mock_aws_client):
        """Test adding expense with empty description"""
        # Mock AWS client
        mock_client_instance = Mock()
        mock_client_instance.download_expenses_from_s3.return_value = []
        mock_aws_client.return_value = mock_client_instance
        
        tracker = ExpenseTracker()
        
        result = tracker.add_expense("", 4.50, "Food")
        
        assert result is False
        assert len(tracker.expenses) == 0
    
    @patch('src.expense_tracker.AWSClient')
    @patch('src.expense_tracker.load_dotenv')
    def test_delete_expense_success(self, mock_load_dotenv, mock_aws_client):
        """Test deleting expense successfully"""
        # Mock AWS client
        mock_client_instance = Mock()
        existing_expenses = [
            {'id': 1, 'description': 'Coffee', 'amount': 4.50, 'category': 'Food'}
        ]
        mock_client_instance.download_expenses_from_s3.return_value = existing_expenses
        mock_client_instance.upload_expenses_to_s3.return_value = True
        mock_aws_client.return_value = mock_client_instance
        
        tracker = ExpenseTracker()
        
        result = tracker.delete_expense(1)
        
        assert result is True
        assert len(tracker.expenses) == 0
        mock_client_instance.upload_expenses_to_s3.assert_called()
    
    @patch('src.expense_tracker.AWSClient')
    @patch('src.expense_tracker.load_dotenv')
    def test_delete_expense_not_found(self, mock_load_dotenv, mock_aws_client):
        """Test deleting non-existent expense"""
        # Mock AWS client
        mock_client_instance = Mock()
        mock_client_instance.download_expenses_from_s3.return_value = []
        mock_aws_client.return_value = mock_client_instance
        
        tracker = ExpenseTracker()
        
        result = tracker.delete_expense(999)
        
        assert result is False
    
    @patch('src.expense_tracker.AWSClient')
    @patch('src.expense_tracker.load_dotenv')
    def test_get_expense_summary(self, mock_load_dotenv, mock_aws_client):
        """Test getting expense summary"""
        # Mock AWS client with existing expenses
        mock_client_instance = Mock()
        existing_expenses = [
            {'id': 1, 'description': 'Coffee', 'amount': 4.50, 'category': 'Food', 'created_at': '2024-01-01T12:00:00'},
            {'id': 2, 'description': 'Gas', 'amount': 45.00, 'category': 'Transport', 'created_at': '2024-01-02T12:00:00'},
            {'id': 3, 'description': 'Lunch', 'amount': 12.00, 'category': 'Food', 'created_at': '2024-01-03T12:00:00'}
        ]
        mock_client_instance.download_expenses_from_s3.return_value = existing_expenses
        mock_aws_client.return_value = mock_client_instance
        
        tracker = ExpenseTracker()
        summary = tracker.get_expense_summary()
        
        assert summary['total_expenses'] == 3
        assert summary['total_amount'] == 61.50
        assert 'Food' in summary['categories']
        assert 'Transport' in summary['categories']
        assert summary['categories']['Food']['count'] == 2
        assert summary['categories']['Food']['amount'] == 16.50
        assert len(summary['recent_expenses']) == 3
    
    @patch('src.expense_tracker.AWSClient')
    @patch('src.expense_tracker.load_dotenv')
    def test_get_expense_summary_empty(self, mock_load_dotenv, mock_aws_client):
        """Test getting summary with no expenses"""
        # Mock AWS client
        mock_client_instance = Mock()
        mock_client_instance.download_expenses_from_s3.return_value = []
        mock_aws_client.return_value = mock_client_instance
        
        tracker = ExpenseTracker()
        summary = tracker.get_expense_summary()
        
        assert summary['total_expenses'] == 0
        assert summary['total_amount'] == 0
        assert summary['categories'] == {}
        assert summary['recent_expenses'] == []


# Integration tests
class TestIntegration:
    """Integration tests for the complete flow"""
    
    @patch('src.expense_tracker.AWSClient')
    @patch('src.expense_tracker.load_dotenv')
    def test_complete_expense_workflow(self, mock_load_dotenv, mock_aws_client):
        """Test complete workflow: add, view, delete expenses"""
        # Mock AWS client
        mock_client_instance = Mock()
        mock_client_instance.download_expenses_from_s3.return_value = []
        mock_client_instance.upload_expenses_to_s3.return_value = True
        mock_aws_client.return_value = mock_client_instance
        
        tracker = ExpenseTracker()
        
        # Add multiple expenses
        assert tracker.add_expense("Coffee", 4.50, "Food") is True
        assert tracker.add_expense("Gas", 45.00, "Transport") is True
        assert tracker.add_expense("Movie", 12.00, "Entertainment") is True
        
        # Check expenses were added
        assert len(tracker.expenses) == 3
        
        # Get summary
        summary = tracker.get_expense_summary()
        assert summary['total_expenses'] == 3
        assert summary['total_amount'] == 61.50
        
        # Delete an expense
        assert tracker.delete_expense(1) is True
        assert len(tracker.expenses) == 2
        
        # Verify upload was called for each operation
        assert mock_client_instance.upload_expenses_to_s3.call_count == 4  # 3 adds + 1 delete


if __name__ == '__main__':
    pytest.main(['-v', __file__])