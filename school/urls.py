from django.urls import path
from .views import login_view, HealthCheckView, login_page, mark_view_page

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('login/', login_view, name='login'), # API endpoint
    path('login-page/', login_page, name='login-page'),  # Login HTML page route
    path('mark-view/', mark_view_page, name='mark-view'), # Mark_view HTML page route
]
