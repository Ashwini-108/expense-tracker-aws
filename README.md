# 💰 Cloud Expense Tracker

A command-line expense tracking application that stores data in AWS S3 and logs activities to CloudWatch.

## ✨ Features

- **Add expenses** with description, amount, and category
- **View expenses** with optional category filtering
- **Delete expenses** by ID
- **Expense summaries** with statistics and recent activity
- **Cloud storage** with AWS S3 for data persistence
- **Activity logging** with AWS CloudWatch for monitoring
- **Automated testing** and deployment with GitHub Actions

## 🛠️ Tech Stack

- **Python 3.8+** - Core application
- **AWS S3** - Data storage
- **AWS CloudWatch** - Activity logging
- **Click** - CLI framework
- **Boto3** - AWS SDK
- **Pytest** - Testing framework
- **GitHub Actions** - CI/CD pipeline

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd expense-tracker
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv expense_env
   
   # Windows
   expense_env\Scripts\activate
   
   # Mac/Linux
   source expense_env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file with your AWS credentials:
   ```bash
   AWS_ACCESS_KEY_ID=your_access_key_here
   AWS_SECRET_ACCESS_KEY=your_secret_key_here
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=your-bucket-name-here
   CLOUDWATCH_LOG_GROUP=expense-tracker-logs
   ```

## 📊 Usage

### Test AWS Connection
```bash
python src/expense_tracker.py test
```

### Add Expenses
```bash
python src/expense_tracker.py add "Coffee" 4.50 --category Food
python src/expense_tracker.py add "Gas" 45.00 --category Transport
python src/expense_tracker.py add "Movie ticket" 12.00 --category Entertainment
```

### View Expenses
```bash
# View all expenses
python src/expense_tracker.py view

# View expenses by category
python src/expense_tracker.py view --category Food
```

### Delete Expenses
```bash
python src/expense_tracker.py delete 1
```

### View Summary
```bash
python src/expense_tracker.py summary
```

### Get Help
```bash
python src/expense_tracker.py --help
python src/expense_tracker.py add --help
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

Run with coverage:
```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

## 🏗️ Project Structure

```
expense-tracker/
├── src/
│   ├── __init__.py
│   ├── expense_tracker.py      # Main application logic
│   └── aws_client.py           # AWS S3 and CloudWatch client
├── tests/
│   └── test_expense_tracker.py # Test suite
├── .github/
│   └── workflows/
│       └── ci-cd.yml           # GitHub Actions CI/CD
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (not in git)
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## 🔐 AWS Setup Required

1. **Create AWS Account** and set up billing
2. **Create IAM User** with programmatic access
3. **Attach Policies**: `AmazonS3FullAccess`, `CloudWatchLogsFullAccess`
4. **Create S3 Bucket** for storing expense data
5. **Configure credentials** in `.env` file

## 🚀 CI/CD Pipeline

The project includes GitHub Actions for:
- **Code linting** with flake8
- **Running tests** with pytest
- **Security scanning** with bandit
- **Automated deployment** (when tests pass)

## 📝 Example Output

```
✅ Expense added successfully!
   💰 $4.5 for 'Coffee' in category 'Food'

💰 All Expenses (3 total):
--------------------------------------------------------------------------------
ID   Date         Amount     Category        Description
--------------------------------------------------------------------------------
1    2024-01-15   $4.50      Food            Coffee
2    2024-01-15   $45.00     Transport       Gas
3    2024-01-15   $12.00     Entertainment   Movie ticket
--------------------------------------------------------------------------------
Total:                      $61.50

📊 Expense Summary:
--------------------------------------------------
Total Expenses: 3
Total Amount: $61.50

📂 By Category:
  • Food: 1 expenses, $4.50
  • Transport: 1 expenses, $45.00
  • Entertainment: 1 expenses, $12.00
```

## 🔍 Monitoring

All application activities are logged to AWS CloudWatch:
- Expense additions and deletions
- Data uploads and downloads
- Error conditions
- User actions

View logs in AWS Console → CloudWatch → Log Groups → `expense-tracker-logs`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues:

**AWS Credentials Error:**
- Verify your `.env` file has correct AWS credentials
- Check IAM user has required permissions
- Ensure AWS region matches your S3 bucket region

**S3 Bucket Access Error:**
- Verify bucket name is correct and unique
- Check bucket region matches AWS_REGION in .env
- Ensure IAM user has S3 permissions

**CloudWatch Logging Issues:**
- Verify IAM user has CloudWatch Logs permissions
- Check if log group exists in AWS Console
- Ensure AWS region is correct

**Module Import Errors:**
- Activate virtual environment: `source expense_env/bin/activate`
- Install requirements: `pip install -r requirements.txt`
- Check Python path and working directory