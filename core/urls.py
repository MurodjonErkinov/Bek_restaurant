from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from kassa.views import CashExpenseViewSet, CashSessionViewSet, CashTransactionViewSet
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
router.register(r'cash-sessions', CashSessionViewSet, basename='cash-session')
router.register(r'cash-expenses', CashExpenseViewSet, basename='cash-expense')
router.register(r'cash-transactions', CashTransactionViewSet, basename='cash-transaction')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('authentication.urls')),
    path('api/', include(router.urls)),
]
