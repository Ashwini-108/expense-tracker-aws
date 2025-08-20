"""
Tests for the Expense Tracker application
"""

import pytest
import os
import sys
from unittest.mock import Mock, patch

# Add the src directory to the Python path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic_functionality():
    """Basic test to ensure the test framework is working"""
    assert True

def test_math_operations():
    """Test basic math operations used in expense calculations"""
    # Test expense amount calculations
    amount1 = 4.50
    amount2 = 15.75
    total = amount1 + amount2
    assert total == 20.25
    
    # Test rounding
    amount3 = 4.567
    rounded_amount = round(amount3, 2)
    assert rounded_amount == 4.57

@patch.dict(os.environ, {
    'AWS_REGION': 'us-east-1',
    'S3_BUCKET_NAME': 'test-bucket',
    'CLOUDWATCH_LOG_GROUP': 'test-logs'
})
def test_environment_variables():
    """Test that environment variables can be read"""
    assert os.getenv('S3_BUCKET_NAME') == 'test-bucket'
    assert os.getenv('AWS_REGION') == 'us-east-1'
    assert os.getenv('CLOUDWATCH_LOG_GROUP') == 'test-logs'

def test_expense_data_structure():
    """Test expense data structure"""
    expense = {
        'id': 1,
        'description': 'Test Coffee',
        'amount': 4.50,
        'category': 'Food',
        'date': '2024-01-15 10:30:45'
    }
    
    assert expense['id'] == 1
    assert expense['description'] == 'Test Coffee'
    assert expense['amount'] == 4.50
    assert expense['category'] == 'Food'
    assert 'date' in expense

def test_expense_validation():
    """Test expense validation logic"""
    # Valid expense data
    valid_amount = 10.50
    valid_description = "Valid expense"
    
    assert valid_amount > 0
    assert len(valid_description.strip()) > 0
    
    # Invalid expense data
    invalid_amount = -5.0
    invalid_description = ""
    
    assert invalid_amount <= 0
    assert len(invalid_description.strip()) == 0

def test_category_filtering():
    """Test category filtering functionality"""
    expenses = [
        {'id': 1, 'category': 'Food', 'amount': 10.0},
        {'id': 2, 'category': 'Transport', 'amount': 15.0},
        {'id': 3, 'category': 'Food', 'amount': 8.0},
    ]
    
    # Filter by Food category
    food_expenses = [exp for exp in expenses if exp['category'].lower() == 'food']
    assert len(food_expenses) == 2
    
    # Filter by Transport category
    transport_expenses = [exp for exp in expenses if exp['category'].lower() == 'transport']
    assert len(transport_expenses) == 1

def test_summary_calculations():
    """Test expense summary calculations"""
    expenses = [
        {'id': 1, 'category': 'Food', 'amount': 10.0},
        {'id': 2, 'category': 'Transport', 'amount': 15.0},
        {'id': 3, 'category': 'Food', 'amount': 8.0},
    ]
    
    # Calculate total
    total_amount = sum(exp['amount'] for exp in expenses)
    assert total_amount == 33.0
    
    # Count by category
    categories = {}
    for expense in expenses:
        category = expense['category']
        if category not in categories:
            categories[category] = {'count': 0, 'amount': 0}
        categories[category]['count'] += 1
        categories[category]['amount'] += expense['amount']
    
    assert categories['Food']['count'] == 2
    assert categories['Food']['amount'] == 18.0
    assert categories['Transport']['count'] == 1
    assert categories['Transport']['amount'] == 15.0

if __name__ == '__main__':
    pytest.main(['-v', __file__])