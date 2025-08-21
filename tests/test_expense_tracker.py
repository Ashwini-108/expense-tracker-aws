# test_expense_tracker.py - Fixed version
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json
import tempfile
import os
from expense_tracker import ExpenseTracker
from aws_client import AWSClient


class TestExpenseTracker(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = ExpenseTracker()


class TestAWSClient(unittest.TestCase):
    @patch('boto3.client')
    def setUp(self, mock_boto_client):
        """Set up test fixtures with mocked AWS client."""
        self.mock_client = MagicMock()
        mock_boto_client.return_value = self.mock_client
        self.cost_explorer = AWSClient()
        self.tracker = ExpenseTracker()

    def test_add_manual_expense(self):
        """Test adding a manual expense."""
        result = self.tracker.add_manual_expense(
            amount=50.0,
            category='Food',
            description='Lunch'
        )
        self.assertTrue(result)
        self.assertEqual(len(self.tracker.expenses_data), 1)
        self.assertEqual(self.tracker.expenses_data[0]['amount'], 50.0)


class TestExpenseAnalysis(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        self.tracker = ExpenseTracker()
        # Add test data
        self.tracker.add_manual_expense(100.0, 'Food', 'Groceries', '2024-01-01')
        self.tracker.add_manual_expense(50.0, 'Transport', 'Gas', '2024-01-02')

    def test_analyze_spending_patterns(self):
        """Test spending pattern analysis."""
        analysis = self.tracker.analyze_spending_patterns()
        self.assertIn('total_expenses', analysis)
        self.assertIn('category_breakdown', analysis)
        self.assertEqual(analysis['total_expenses'], 150.0)


class TestReportGeneration(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        self.tracker = ExpenseTracker()
        self.tracker.add_manual_expense(100.0, 'Food', 'Test expense')

    def test_generate_json_report(self):
        """Test JSON report generation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_filename = f.name

        try:
            result = self.tracker.generate_expense_report('json', temp_filename)
            self.assertEqual(result, temp_filename)
            self.assertTrue(os.path.exists(temp_filename))

            # Verify content
            with open(temp_filename, 'r') as f:
                data = json.load(f)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]['amount'], 100.0)

        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)


class TestAWSIntegration(unittest.TestCase):
    @patch('boto3.client')
    def setUp(self, mock_boto_client):
        """Set up mocked AWS integration tests."""
        self.mock_client = MagicMock()
        mock_boto_client.return_value = self.mock_client
        self.tracker = ExpenseTracker()

    def test_fetch_aws_costs_success(self):
        """Test successful AWS cost fetching."""
        # Mock response
        mock_response = {
            'ResultsByTime': [
                {
                    'TimePeriod': {'Start': '2024-01-01', 'End': '2024-01-02'},
                    'Groups': [
                        {
                            'Keys': ['Amazon EC2-Instance'],
                            'Metrics': {
                                'BlendedCost': {'Amount': '10.50', 'Unit': 'USD'}
                            }
                        }
                    ]
                }
            ]
        }

        self.tracker.cost_explorer.client.get_cost_and_usage.return_value = mock_response
        result = self.tracker.fetch_aws_costs(days_back=1)

        self.assertIn('daily_costs', result)
        self.assertIn('service_costs', result)
        self.assertIn('total_cost', result)


if __name__ == '__main__':
    unittest.main()
