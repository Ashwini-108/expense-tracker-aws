# expense_tracker.py - Fixed version
import json
import csv
from datetime import datetime, timedelta
from typing import Dict


import pandas as pd
import matplotlib.pyplot as plt


# Module level imports should be at the top
from aws_client import AWSClient


class ExpenseTracker:
    def __init__(self, aws_region: str = "us-east-1"):
        """Initialize the expense tracker with AWS Cost Explorer."""
        self.cost_explorer = AWSClient(region_name=aws_region)
        self.expenses_data = []

    def add_manual_expense(
            self,
            amount: float,
            category: str,
            description: str,
            date: str = None) -> bool:
        """
        Add a manual expense entry.

        Args:
            amount: Expense amount
            category: Expense category
            description: Expense description
            date: Date in YYYY-MM-DD format (defaults to today)

        Returns:
            True if successful, False otherwise
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        expense = {
            "date": date,
            "amount": amount,
            "category": category,
            "description": description,
            "source": "manual"}

        self.expenses_data.append(expense)
        return True

    def fetch_aws_costs(self, days_back: int = 30) -> Dict:
        """
        Fetch AWS costs for the specified number of days.

        Args:
            days_back: Number of days to look back

        Returns:
            Dictionary containing AWS cost data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        try:
            cost_data = self.cost_explorer.get_cost_and_usage(
                start_date=start_str, end_date=end_str, granularity="DAILY"
            )

            # Process the AWS cost data
            processed_costs = self._process_aws_cost_data(cost_data)
            return processed_costs

        except Exception as e:
            print(f"Error fetching AWS costs: {e}")
            return {}

    def _process_aws_cost_data(self, cost_data: Dict) -> Dict:
        """Process raw AWS cost data into a more usable format."""
        processed = {"daily_costs": [], "service_costs": {}, "total_cost": 0}

        if "ResultsByTime" not in cost_data:
            return processed

        for result in cost_data["ResultsByTime"]:
            date = result["TimePeriod"]["Start"]
            daily_total = 0

            for group in result["Groups"]:
                service = group["Keys"][0]
                cost = float(group["Metrics"]["BlendedCost"]["Amount"])

                if service not in processed["service_costs"]:
                    processed["service_costs"][service] = 0
                processed["service_costs"][service] += cost
                daily_total += cost

            processed["daily_costs"].append(
                {"date": date, "amount": daily_total})
            processed["total_cost"] += daily_total

        return processed

    def generate_expense_report(
            self,
            output_format: str = "json",
            filename: str = None) -> str:
        """
        Generate an expense report.

        Args:
            output_format: 'json' or 'csv'
            filename: Output filename (optional)

        Returns:
            String representation of the report or filename if saved
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"expense_report_{timestamp}.{output_format}"

        try:
            if output_format.lower() == "json":
                with open(filename, "w") as f:
                    json.dump(self.expenses_data, f, indent=2)
            elif output_format.lower() == "csv":
                if self.expenses_data:
                    df = pd.DataFrame(self.expenses_data)
                    df.to_csv(filename, index=False)
                else:
                    # Create empty CSV with headers
                    with open(filename, "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(
                            ["date", "amount", "category", "description", "source"])

            return filename

        except Exception as e:
            print(f"Error generating report: {e}")
            return ""

    def analyze_spending_patterns(self) -> Dict:
        """Analyze spending patterns from the collected data."""
        if not self.expenses_data:
            return {"message": "No expense data available for analysis"}

        df = pd.DataFrame(self.expenses_data)
        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

        analysis = {
            "total_expenses": df["amount"].sum(),
            "average_daily_spend": df.groupby(
                df["date"].dt.date)["amount"].sum().mean(),
            "category_breakdown": df.groupby("category")["amount"].sum().to_dict(),
            "highest_expense_day": df.groupby(
                df["date"].dt.date)["amount"].sum().idxmax(),
            "expense_trend": self._calculate_trend(df),
        }

        return analysis

    def _calculate_trend(self, df: pd.DataFrame) -> str:
        """Calculate spending trend over time."""
        daily_totals = df.groupby(df["date"].dt.date)["amount"].sum()
        if len(daily_totals) < 2:
            return "insufficient_data"

        recent_avg = daily_totals.tail(7).mean()
        older_avg = daily_totals.head(7).mean()

        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

    def create_visualization(
            self,
            chart_type: str = "daily",
            save_path: str = None):
        """
        Create visualizations of expense data.

        Args:
            chart_type: 'daily', 'category', or 'trend'
            save_path: Path to save the chart (optional)
        """
        if not self.expenses_data:
            print("No data available for visualization")
            return

        df = pd.DataFrame(self.expenses_data)
        df["date"] = pd.to_datetime(df["date"])
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

        plt.figure(figsize=(12, 6))

        if chart_type == "daily":
            daily_totals = df.groupby(df["date"].dt.date)["amount"].sum()
            plt.plot(daily_totals.index, daily_totals.values, marker="o")
            plt.title("Daily Expenses")
            plt.xlabel("Date")
            plt.ylabel("Amount ($)")
            plt.xticks(rotation=45)

        elif chart_type == "category":
            category_totals = df.groupby("category")["amount"].sum()
            plt.pie(
                category_totals.values,
                labels=category_totals.index,
                autopct="%1.1f%%")
            plt.title("Expenses by Category")

        elif chart_type == "trend":
            df_monthly = df.groupby(
                df["date"].dt.to_period("M"))["amount"].sum()
            plt.bar(range(len(df_monthly)), df_monthly.values)
            plt.title("Monthly Expense Trends")
