# aws_client.py - Fixed version
import boto3

from typing import Dict, List

from botocore.exceptions import ClientError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AWSClient:
    def __init__(self, region_name: str = 'us-east-1'):
        """Initialize AWS Cost Explorer client."""
        try:
            self.client = boto3.client('ce', region_name=region_name)
            logger.info("AWS Cost Explorer client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            raise

    def get_cost_and_usage(self, start_date: str, end_date: str,
                          granularity: str = 'DAILY',
                          metrics: List[str] = None) -> Dict:
        """
        Get cost and usage data from AWS Cost Explorer.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: DAILY, MONTHLY, or HOURLY
            metrics: List of metrics to retrieve

        Returns:
            Dictionary containing cost and usage data
        """
        if metrics is None:
            metrics = ['BlendedCost', 'UsageQuantity']

        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=metrics,
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }
                ]
            )
            logger.info(f"Successfully retrieved cost data for {start_date} to {end_date}")
            return response

        except ClientError as e:
            logger.error(f"AWS API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def get_dimension_values(self, dimension: str, start_date: str, end_date: str) -> List[str]:
        """
        Get possible values for a dimension.

        Args:
            dimension: The dimension to get values for (e.g., 'SERVICE', 'LINKED_ACCOUNT')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of dimension values
        """
        try:
            response = self.client.get_dimension_values(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Dimension=dimension
            )
            return [item['Value'] for item in response['DimensionValues']]

        except ClientError as e:
            logger.error(f"Failed to get dimension values: {e}")
            raise

    def get_usage_forecast(self, start_date: str, end_date: str, metric: str = 'BLENDED_COST') -> Dict:
        """
        Get usage forecast from AWS Cost Explorer.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            metric: Metric to forecast

        Returns:
            Dictionary containing forecast data
        """
        try:
            response = self.client.get_usage_forecast(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Metric=metric,
                Granularity='DAILY'
            )
            logger.info(f"Successfully retrieved forecast data for {start_date} to {end_date}")
            return response

        except ClientError as e:
            logger.error(f"Failed to get usage forecast: {e}")
            raise

    def get_rightsizing_recommendation(self) -> Dict:
        """Get rightsizing recommendations."""
        try:
            response = self.client.get_rightsizing_recommendation(
                Service='AmazonEC2'
            )
            return response

        except ClientError as e:
            logger.error(f"Failed to get rightsizing recommendations: {e}")
            raise

    def get_cost_categories(self) -> List[Dict]:
        """Get all cost categories."""
        try:
            response = self.client.list_cost_category_definitions()
            return response['CostCategoryReferences']

        except ClientError as e:
            logger.error(f"Failed to get cost categories: {e}")
            raise

    def create_cost_budget_alert(self, budget_name: str, budget_limit: float,
                                email_address: str, time_unit: str = 'MONTHLY') -> Dict:
        """
        Create a cost budget with email alerts.

        Args:
            budget_name: Name for the budget
            budget_limit: Budget limit amount
            email_address: Email address for notifications
            time_unit: MONTHLY, QUARTERLY, or ANNUALLY

        Returns:
            Dictionary containing budget creation response
        """
        budgets_client = boto3.client('budgets')

        budget = {
            'BudgetName': budget_name,
            'BudgetLimit': {
                'Amount': str(budget_limit),
                'Unit': 'USD'
            },
            'TimeUnit': time_unit,
            'BudgetType': 'COST'
        }

        notification = {
            'NotificationType': 'ACTUAL',
            'ComparisonOperator': 'GREATER_THAN',
            'Threshold': 80.0,
            'ThresholdType': 'PERCENTAGE'
        }

        subscriber = {
            'SubscriptionType': 'EMAIL',
            'Address': email_address
        }

        try:
            response = budgets_client.create_budget(
                AccountId='123456789012',  # Replace with actual account ID
                Budget=budget,
                NotificationsWithSubscribers=[
                    {
                        'Notification': notification,
                        'Subscribers': [subscriber]
                    }
                ]
            )
            logger.info(f"Budget '{budget_name}' created successfully")
            return response

        except ClientError as e:
            logger.error(f"Failed to create budget: {e}")
            raise
