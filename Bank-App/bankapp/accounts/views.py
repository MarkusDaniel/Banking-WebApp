from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.contrib import messages
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from .models import BankAccount, Transaction

from django.shortcuts import redirect
import random
def delete_all_accounts(request):
    if request.user.is_superuser:  # Optional: Restrict this action to admins
        BankAccount.objects.all().delete()  # Delete all records
        messages.success(request, "All accounts have been deleted successfully.")
    else:
        messages.error(request, "You don't have permission to delete accounts.")
    return redirect('home')
# Function to generate a unique account number
def generate_unique_account_number():
    while True:
        account_number = str(random.randint(100000, 999999))  # Generate a 6-digit number
        if not BankAccount.objects.filter(account_number=account_number).exists():
            return account_number

# Home view
def home(request):
    return render(request, 'accounts/home.html')

# Register view
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Create a BankAccount for the user
            account_number = generate_unique_account_number()  # Use the helper function
            BankAccount.objects.create(
                account_number=account_number,
                account_holder=user.username,  # Assuming username is the account holder
                balance=0.00  # Set an initial balance
            )

            messages.success(request, "Registration successful! Account created.")
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})

# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Fetch the BankAccount linked to the user after login
            try:
                account = BankAccount.objects.get(account_holder=user.username)
                messages.success(request, "Login successful!")
                return redirect('account_detail', account_number=account.account_number)
            except BankAccount.DoesNotExist:
                messages.error(request, "No account linked to this user.")
                return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'accounts/login.html', {'form': form})

# Logout view
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

# Account detail view (requires login)
@login_required
def account_detail(request, account_number):
    try:
        account = BankAccount.objects.get(account_number=account_number, account_holder=request.user.username)
    except BankAccount.DoesNotExist:
        return redirect('home')  # Redirect if account doesn't exist or doesn't belong to the user
    return render(request, 'accounts/account_detail.html', {'account': account})

from django.shortcuts import get_object_or_404

# Transactions view
@login_required
def transactions(request, account_number):
    # Fetch the bank account, or redirect if not found
    account = get_object_or_404(BankAccount, account_number=account_number, account_holder=request.user.username)
    
    # Fetch the related transactions, with filters if provided
    transactions = Transaction.objects.filter(account=account)

    # Apply filters if any
    category = request.GET.get('category')
    if category:
        transactions = transactions.filter(category=category)

    transaction_type = request.GET.get('transaction_type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    start_date = request.GET.get('start_date')
    if start_date:
        transactions = transactions.filter(transaction_date__gte=start_date)

    end_date = request.GET.get('end_date')
    if end_date:
        transactions = transactions.filter(transaction_date__lte=end_date)

    # Order by the latest transaction first
    transactions = transactions.order_by('-transaction_date')

    # Render the template with account and transactions data
    return render(request, 'accounts/transactions.html', {'account': account, 'transactions': transactions})


#Transfer
@login_required
def transfer(request, account_number):
    account = BankAccount.objects.get(account_number=account_number, account_holder=request.user.username)
    
    if request.method == 'POST':
        recipient_account_number = request.POST['recipient_account_number']
        amount = int(request.POST['amount'])  # Ensure it's an integer
        category = request.POST.get('category', 'others')  # Get the selected category, default to 'others'
        
        if account.balance < amount:
            messages.error(request, "Insufficient balance to make a transfer.")
            return redirect('transfer', account_number=account.account_number)
        
        try:
            recipient = BankAccount.objects.get(account_number=recipient_account_number)
            
            # Deduct the amount from the sender (negative transaction)
            account.balance -= amount
            account.save()

            # Add the amount to the recipient (positive transaction)
            recipient.balance += amount
            recipient.save()

            # Create a transaction for the sender (negative amount)
            Transaction.objects.create(
                transaction_type='transfer',
                account=account,
                amount=-amount,  # Negative transaction for the sender
                category=category  # Save the category
            )

            # Create a transaction for the recipient (positive amount)
            Transaction.objects.create(
                transaction_type='transfer',
                account=recipient,
                amount=amount,  # Positive transaction for the recipient
                category=category  # Save the category
            )

            messages.success(request, "Transfer successful.")
        except BankAccount.DoesNotExist:
            messages.error(request, "Recipient account not found.")
    
    return render(request, 'accounts/transfer.html', {'account': account})



# Cashup view
@login_required
def cashup(request, account_number):
    account = BankAccount.objects.get(account_number=account_number, account_holder=request.user.username)
    
    if request.method == 'POST':
        amount = int(request.POST['amount'])  # Only allow integers for cashup
        account.balance += amount
        account.save()

        # Create a transaction for the cashup, category set to "others"
        Transaction.objects.create(
            transaction_type='deposit',  # It's a deposit, so transaction type is 'deposit'
            account=account,
            amount=amount,
            category='others'  # Automatically set category to "others"
        )
        
        messages.success(request, "Your account has been updated with cash.")
        return redirect('account_detail', account_number=account.account_number)

    return render(request, 'accounts/cashup.html', {'account': account})


# Cash withdrawal view
@login_required
def withdraw(request, account_number):
    account = get_object_or_404(BankAccount, account_number=account_number, account_holder=request.user.username)

    if request.method == 'POST':
        try:
            amount = int(request.POST['amount'])  # Ensure it's an integer
            if amount <= 0:
                messages.error(request, "Withdrawal amount must be positive.")
                return redirect('withdraw', account_number=account.account_number)

            if account.balance < amount:
                messages.error(request, "Insufficient balance for withdrawal.")
                return redirect('withdraw', account_number=account.account_number)

            # Update the account balance
            account.balance -= amount
            account.save()

            # Create a transaction for the withdrawal, category set to "others"
            Transaction.objects.create(
                transaction_type='withdrawal',
                account=account,
                amount=-amount,
                category='others'  # Automatically set category to "others"
            )

            messages.success(request, f"Withdrawal of ${amount} successful.")
            return redirect('account_detail', account_number=account.account_number)

        except ValueError:
            messages.error(request, "Invalid amount entered.")
            return redirect('withdraw', account_number=account.account_number)

    return render(request, 'accounts/withdraw.html', {'account': account})

# PDF Export View (Filtered)
@login_required
def export_transactions_pdf(request, account_number):
    account = BankAccount.objects.get(account_number=account_number, account_holder=request.user.username)
    transactions = Transaction.objects.filter(account=account)

    # Apply filters if any
    category = request.GET.get('category')
    if category:
        transactions = transactions.filter(category=category)

    transaction_type = request.GET.get('transaction_type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    start_date = request.GET.get('start_date')
    if start_date:
        transactions = transactions.filter(transaction_date__gte=start_date)

    end_date = request.GET.get('end_date')
    if end_date:
        transactions = transactions.filter(transaction_date__lte=end_date)

    # Create an HTTP response with the PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transactions_{account_number}.pdf"'

    # Create the PDF object
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Add title to the PDF
    p.setFont("Helvetica", 12)
    p.drawString(200, height - 50, f"Transactions for Account: {account_number}")

    # Add column headers
    y_position = height - 100
    p.drawString(50, y_position, "Transaction Type")
    p.drawString(200, y_position, "Category")
    p.drawString(350, y_position, "Amount")
    p.drawString(500, y_position, "Date")

    # Add the transactions
    y_position -= 20
    for transaction in transactions:
        p.drawString(50, y_position, transaction.transaction_type)
        p.drawString(200, y_position, transaction.category)
        p.drawString(350, y_position, f"${transaction.amount}")
        p.drawString(500, y_position, transaction.transaction_date.strftime('%Y-%m-%d'))
        y_position -= 20

    # Save the PDF
    p.showPage()
    p.save()

    return response