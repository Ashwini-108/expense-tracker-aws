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
        'S3_BUCKET_NAME': 'test-bucket',
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
        
        assert client.s3_bucket == 'test-bucket'
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
        'S3_BUCKET_NAME': 'test-bucket',
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
        'S3_BUCKET_NAME': 'test-bucket',
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
        'S3_BUCKET_NAME': 'test-bucket',
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
    """Test Expense Tracker functionality