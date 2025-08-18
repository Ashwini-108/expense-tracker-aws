"""
AWS Client Module
Handles all AWS operations - S3 file storage and CloudWatch logging
"""

import boto3
import json
import os
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError


class AWSClient:
    """
    Manages AWS S3 and CloudWatch operations for the expense tracker
    """
    
    def __init__(self):
        """Initialize AWS clients and configuration"""
        try:
            # Get configuration from environment variables
            self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
            self.s3_bucket = os.getenv('S3_BUCKET_NAME')
            self.log_group = os.getenv('CLOUDWATCH_LOG_GROUP', 'expense-tracker-logs')
            
            # Validate required environment variables
            if not self.s3_bucket:
                raise ValueError("S3_BUCKET_NAME environment variable is required")
            
            # Initialize AWS clients
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
            self.cloudwatch_client = boto3.client('logs', region_name=self.aws_region)
            
            # Ensure CloudWatch log group exists
            self._create_log_group_if_not_exists()
            
        except NoCredentialsError:
            raise Exception("AWS credentials not found. Please check your .env file.")
        except Exception as e:
            raise Exception(f"Failed to initialize AWS client: {str(e)}")
    
    def _create_log_group_if_not_exists(self):
        """Create CloudWatch log group if it doesn't exist"""
        try:
            self.cloudwatch_client.create_log_group(logGroupName=self.log_group)
            print(f"Created CloudWatch log group: {self.log_group}")
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                raise e
            # Log group already exists, which is fine
    
    def upload_expenses_to_s3(self, expenses_data, user_id="default"):
        """
        Upload expenses data to S3 as JSON file
        
        Args:
            expenses_data (list): List of expense dictionaries
            user_id (str): User identifier for file naming
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert expenses to JSON string
            json_data = json.dumps(expenses_data, indent=2, default=str)
            
            # Create file key (path) in S3
            file_key = f"expenses/{user_id}/expenses.json"
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=file_key,
                Body=json_data,
                ContentType='application/json'
            )
            
            # Log the action
            self.log_action("UPLOAD", f"Uploaded expenses for user {user_id} to S3")
            return True
            
        except Exception as e:
            self.log_action("ERROR", f"Failed to upload to S3: {str(e)}")
            return False
    
    def download_expenses_from_s3(self, user_id="default"):
        """
        Download expenses data from S3
        
        Args:
            user_id (str): User identifier
            
        Returns:
            list: List of expenses or empty list if file doesn't exist
        """
        try:
            file_key = f"expenses/{user_id}/expenses.json"
            
            # Download from S3
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=file_key
            )
            
            # Parse JSON data
            json_data = response['Body'].read().decode('utf-8')
            expenses = json.loads(json_data)
            
            self.log_action("DOWNLOAD", f"Downloaded expenses for user {user_id} from S3")
            return expenses
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                # File doesn't exist yet, return empty list
                self.log_action("INFO", f"No expenses file found for user {user_id}, returning empty list")
                return []
            else:
                self.log_action("ERROR", f"Failed to download from S3: {str(e)}")
                return []
        except Exception as e:
            self.log_action("ERROR", f"Failed to download from S3: {str(e)}")
            return []
    
    def log_action(self, level, message):
        """
        Log action to CloudWatch Logs
        
        Args:
            level (str): Log level (INFO, ERROR, WARNING, etc.)
            message (str): Log message
        """
        try:
            # Create log stream name with current date
            log_stream = f"expense-tracker-{datetime.now().strftime('%Y-%m-%d')}"
            
            # Try to create log stream (it's okay if it already exists)
            try:
                self.cloudwatch_client.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=log_stream
                )
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceAlreadyExistsException':
                    raise e
            
            # Create log event
            log_event = {
                'timestamp': int(datetime.now().timestamp() * 1000),  # CloudWatch expects milliseconds
                'message': f"[{level}] {datetime.now().isoformat()} - {message}"
            }
            
            # Put log event
            self.cloudwatch_client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=log_stream,
                logEvents=[log_event]
            )
            
        except Exception as e:
            print(f"Failed to log to CloudWatch: {str(e)}")
            # Don't raise exception - logging failure shouldn't break the app
    
    def test_connection(self):
        """
        Test AWS connections
        
        Returns:
            dict: Status of S3 and CloudWatch connections
        """
        status = {
            's3': False,
            'cloudwatch': False,
            'errors': []
        }
        
        # Test S3 connection
        try:
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            status['s3'] = True
        except Exception as e:
            status['errors'].append(f"S3 Error: {str(e)}")
        
        # Test CloudWatch connection
        try:
            self.cloudwatch_client.describe_log_groups(
                logGroupNamePrefix=self.log_group,
                limit=1
            )
            status['cloudwatch'] = True
        except Exception as e:
            status['errors'].append(f"CloudWatch Error: {str(e)}")
        
        return status