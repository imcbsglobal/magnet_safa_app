from django.urls import path
from .views import login_view, HealthCheckView, login_page, mark_view_page, FilteredMarksView, MarkFilterMetadata, UpdateMarkView, BulkUpdateMarkView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('login/', login_view, name='login'),
    path('login-page/', login_page, name='login-page'),
    path('mark-view/', mark_view_page, name='mark-view'),
    path('marks/', FilteredMarksView.as_view(), name='filtered-marks'),
    path('filters/', MarkFilterMetadata.as_view(), name='filter-metadata'),
    path('update-mark/', UpdateMarkView.as_view(), name='update-mark'),
    path('bulk_update/', BulkUpdateMarkView.as_view(), name='bulk_mark_update'),
]