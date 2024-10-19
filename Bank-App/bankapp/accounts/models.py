from django.db import models

class BankAccount(models.Model):
    account_number = models.CharField(max_length=12, unique=True)
    account_holder = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.account_holder} ({self.account_number})'

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer', 'Transfer'),
    )

    TRANSACTION_CATEGORIES = (
        ('food', 'Food'),
        ('entertainment', 'Entertainment'),
        ('utilities', 'Utilities'),
        ('others', 'Others'),
    )

    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=TRANSACTION_CATEGORIES, default='others')  # New category field
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.transaction_type} - {self.amount} ({self.category})'
