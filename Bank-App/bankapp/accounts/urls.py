from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Home page route for root URL
    path('accounts/<str:account_number>/', views.account_detail, name='account_detail'),
    path('register/', views.register, name='register'),  # Register route
    path('login/', views.login_view, name='login'),  # Login route
    path('logout/', views.logout_view, name='logout'),  # Logout route
    path('transactions/<str:account_number>/', views.transactions, name='transactions'),  # Transactions route
    path('transfer/<str:account_number>/', views.transfer, name='transfer'),  # Transfer route
    path('cashup/<str:account_number>/', views.cashup, name='cashup'),  # Cashup route
    path('withdraw/<str:account_number>/', views.withdraw, name='withdraw'), #Withdraw
    path('transactions/export/pdf/<str:account_number>/', views.export_transactions_pdf, name='export_transactions_pdf'),
]
