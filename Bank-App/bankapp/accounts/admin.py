from django.contrib import admin
from .models import BankAccount

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'account_holder', 'balance', 'created_at')
    search_fields = ('account_number', 'account_holder')

    # Add custom actions like deleting all accounts
    actions = ['delete_all_accounts']

    # Custom action to delete all accounts
    def delete_all_accounts(self, request, queryset):
        BankAccount.objects.all().delete()
        self.message_user(request, "All accounts have been deleted.")
    delete_all_accounts.short_description = "Delete all bank accounts"
