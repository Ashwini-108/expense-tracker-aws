"""
Expense Tracker CLI Application
Main application logic for managing expenses
"""

import os
import sys
from datetime import datetime
from typing import List, Dict, Optional
import click
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aws_client import AWSClient


class ExpenseTracker:
    """
    Main expense tracker class that handles all expense operations
    """
    
    def __init__(self):
        """Initialize the expense tracker with AWS client"""
        try:
            # Load environment variables from .env file
            load_dotenv()
            
            # Initialize AWS client
            self.aws_client = AWSClient()
            self.user_id = "default"  # In a real app, this would be user login
            
            # Load existing expenses from S3
            self.expenses = self.aws_client.download_expenses_from_s3(self.user_id)
            
            print("✅ Expense Tracker initialized successfully!")
            
        except Exception as e:
            print(f"❌ Failed to initialize Expense Tracker: {str(e)}")
            sys.exit(1)
    
    def add_expense(self, description: str, amount: float, category: str = "Other") -> bool:
        """
        Add a new expense
        
        Args:
            description (str): What you spent money on
            amount (float): How much you spent
            category (str): Category of expense
            
        Returns:
            bool: True if successful
        """
        try:
            # Validate input
            if amount <= 0:
                print("❌ Amount must be greater than 0")
                return False
            
            if not description.strip():
                print("❌ Description cannot be empty")
                return False
            
            # Create expense object
            expense = {
                'id': len(self.expenses) + 1,  # Simple ID generation
                'description': description.strip(),
                'amount': round(amount, 2),  # Round to 2 decimal places
                'category': category.strip(),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'created_at': datetime.now().isoformat()
            }
            
            # Add to local list
            self.expenses.append(expense)
            
            # Save to S3
            if self.aws_client.upload_expenses_to_s3(self.expenses, self.user_id):
                self.aws_client.log_action(
                    "ADD_EXPENSE", 
                    f"Added expense: {description} - ${amount} ({category})"
                )
                print(f"✅ Expense added successfully!")
                print(f"   💰 ${amount} for '{description}' in category '{category}'")
                return True
            else:
                # Remove from local list if S3 upload failed
                self.expenses.pop()
                print("❌ Failed to save expense to cloud storage")
                return False
                
        except Exception as e:
            print(f"❌ Error adding expense: {str(e)}")
            return False
    
    def view_expenses(self, category_filter: Optional[str] = None) -> None:
        """
        Display all expenses or filtered by category
        
        Args:
            category_filter (str, optional): Filter by this category
        """
        try:
            if not self.expenses:
                print("📝 No expenses found. Add your first expense!")
                return
            
            # Filter expenses if category specified
            if category_filter:
                filtered_expenses = [
                    exp for exp in self.expenses 
                    if exp['category'].lower() == category_filter.lower()
                ]
                if not filtered_expenses:
                    print(f"📝 No expenses found in category '{category_filter}'")
                    return
                expenses_to_show = filtered_expenses
                print(f"\n💰 Expenses in category '{category_filter}':")
            else:
                expenses_to_show = self.expenses
                print(f"\n💰 All Expenses ({len(self.expenses)} total):")
            
            # Display expenses in a nice format
            total = 0
            print("-" * 80)
            print(f"{'ID':<4} {'Date':<12} {'Amount':<10} {'Category':<15} {'Description'}")
            print("-" * 80)
            
            for expense in expenses_to_show:
                print(f"{expense['id']:<4} "
                      f"{expense['date'][:10]:<12} "
                      f"${expense['amount']:<9.2f} "
                      f"{expense['category']:<15} "
                      f"{expense['description']}")
                total += expense['amount']
            
            print("-" * 80)
            print(f"{'Total:':<31} ${total:.2f}")
            
            # Log the view action
            self.aws_client.log_action(
                "VIEW_EXPENSES", 
                f"Viewed expenses, filter: {category_filter or 'None'}, count: {len(expenses_to_show)}"
            )
            
        except Exception as e:
            print(f"❌ Error viewing expenses: {str(e)}")
    
    def delete_expense(self, expense_id: int) -> bool:
        """
        Delete an expense by ID
        
        Args:
            expense_id (int): ID of expense to delete
            
        Returns:
            bool: True if successful
        """
        try:
            # Find expense with matching ID
            expense_to_delete = None
            for i, expense in enumerate(self.expenses):
                if expense['id'] == expense_id:
                    expense_to_delete = self.expenses.pop(i)
                    break
            
            if not expense_to_delete:
                print(f"❌ No expense found with ID {expense_id}")
                return False
            
            # Save updated list to S3
            if self.aws_client.upload_expenses_to_s3(self.expenses, self.user_id):
                self.aws_client.log_action(
                    "DELETE_EXPENSE", 
                    f"Deleted expense ID {expense_id}: {expense_to_delete['description']} - ${expense_to_delete['amount']}"
                )
                print(f"✅ Expense deleted successfully!")
                print(f"   🗑️ Removed: {expense_to_delete['description']} - ${expense_to_delete['amount']}")
                return True
            else:
                # Re-add expense if S3 upload failed
                self.expenses.append(expense_to_delete)
                print("❌ Failed to delete expense from cloud storage")
                return False
                
        except Exception as e:
            print(f"❌ Error deleting expense: {str(e)}")
            return False
    
    def get_expense_summary(self) -> Dict:
        """
        Get summary statistics of expenses
        
        Returns:
            dict: Summary data
        """
        try:
            if not self.expenses:
                return {
                    'total_expenses': 0,
                    'total_amount': 0,
                    'categories': {},
                    'recent_expenses': []
                }
            
            # Calculate totals
            total_amount = sum(exp['amount'] for exp in self.expenses)
            
            # Group by categories
            categories = {}
            for expense in self.expenses:
                category = expense['category']
                if category not in categories:
                    categories[category] = {'count': 0, 'amount': 0}
                categories[category]['count'] += 1
                categories[category]['amount'] += expense['amount']
            
            # Get recent expenses (last 5)
            recent_expenses = sorted(
                self.expenses, 
                key=lambda x: x['created_at'], 
                reverse=True
            )[:5]
            
            summary = {
                'total_expenses': len(self.expenses),
                'total_amount': round(total_amount, 2),
                'categories': categories,
                'recent_expenses': recent_expenses
            }
            
            self.aws_client.log_action("VIEW_SUMMARY", "Generated expense summary")
            return summary
            
        except Exception as e:
            print(f"❌ Error generating summary: {str(e)}")
            return {}
    
    def display_summary(self) -> None:
        """Display formatted expense summary"""
        summary = self.get_expense_summary()
        
        if not summary:
            return
        
        print("\n📊 Expense Summary:")
        print("-" * 50)
        print(f"Total Expenses: {summary['total_expenses']}")
        print(f"Total Amount: ${summary['total_amount']:.2f}")
        
        if summary['categories']:
            print("\n📂 By Category:")
            for category, data in summary['categories'].items():
                print(f"  • {category}: {data['count']} expenses, ${data['amount']:.2f}")
        
        if summary['recent_expenses']:
            print("\n🕒 Recent Expenses:")
            for expense in summary['recent_expenses']:
                print(f"  • {expense['date'][:10]} - {expense['description']} (${expense['amount']:.2f})")


# CLI Commands using Click
@click.group()
@click.pass_context
def cli(ctx):
    """💰 Expense Tracker - Manage your expenses in the cloud!"""
    try:
        ctx.ensure_object(dict)
        ctx.obj['tracker'] = ExpenseTracker()
    except Exception as e:
        print(f"Failed to initialize: {e}")
        sys.exit(1)


@cli.command()
@click.argument('description')
@click.argument('amount', type=float)
@click.option('--category', '-c', default='Other', help='Expense category')
@click.pass_context
def add(ctx, description, amount, category):
    """Add a new expense. Example: add "Coffee" 4.50 --category Food"""
    tracker = ctx.obj['tracker']
    tracker.add_expense(description, amount, category)


@cli.command()
@click.option('--category', '-c', help='Filter by category')
@click.pass_context
def view(ctx, category):
    """View all expenses or filter by category"""
    tracker = ctx.obj['tracker']
    tracker.view_expenses(category)


@cli.command()
@click.argument('expense_id', type=int)
@click.pass_context
def delete(ctx, expense_id):
    """Delete an expense by ID"""
    tracker = ctx.obj['tracker']
    tracker.delete_expense(expense_id)


@cli.command()
@click.pass_context
def summary(ctx):
    """Show expense summary and statistics"""
    tracker = ctx.obj['tracker']
    tracker.display_summary()


@cli.command()
@click.pass_context
def test(ctx):
    """Test AWS connections"""
    tracker = ctx.obj['tracker']
    status = tracker.aws_client.test_connection()
    
    print("\n🔍 AWS Connection Test:")
    print("-" * 30)
    print(f"S3 Connection: {'✅' if status['s3'] else '❌'}")
    print(f"CloudWatch Connection: {'✅' if status['cloudwatch'] else '❌'}")
    
    if status['errors']:
        print("\nErrors:")
        for error in status['errors']:
            print(f"  • {error}")


if __name__ == '__main__':
    cli()