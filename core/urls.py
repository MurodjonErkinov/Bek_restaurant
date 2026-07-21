"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from kassa.views import CashExpenseViewSet, CashSessionViewSet, CashTransactionViewSet
from kpi.views import WaiterKPIViewSet
from restaurant.views import (
    CategoryViewSet,
    CustomerViewSet,
    OrderViewSet,
    ProductViewSet,
    RestaurantTableViewSet,
    WaiterViewSet,
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'waiters', WaiterViewSet, basename='waiter')
router.register(r'tables', RestaurantTableViewSet, basename='table')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'waiter-kpis', WaiterKPIViewSet, basename='waiter-kpi')
router.register(r'cash-sessions', CashSessionViewSet, basename='cash-session')
router.register(r'cash-expenses', CashExpenseViewSet, basename='cash-expense')
router.register(r'cash-transactions', CashTransactionViewSet, basename='cash-transaction')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]
