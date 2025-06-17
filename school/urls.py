from django.urls import path
from .views import login_view, HealthCheckView, login_page, mark_view_page, FilteredMarksView, MarkFilterMetadata

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('login/', login_view, name='login'),
    path('login-page/', login_page, name='login-page'),
    path('mark-view/', mark_view_page, name='mark-view'),
    path('marks/', FilteredMarksView.as_view(), name='filtered-marks'),
    path('filters/', MarkFilterMetadata.as_view(), name='filter-metadata'),
]