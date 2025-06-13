from django.urls import path
from . import views

urlpatterns = [
    # Health check endpoint
    path('health/', views.HealthCheckView.as_view(), name='health_check'),

    # Reset sync session
    path('reset-sync-session/', views.ResetSyncSessionView.as_view(),
         name='reset_sync_session'),

    # NEW: Optimized bulk sync endpoint (recommended)
    path('bulk-sync/', views.BulkSyncDataView.as_view(), name='bulk_sync_data'),

    # Legacy sync endpoint (kept for backward compatibility)
    path('sync/', views.SyncDataView.as_view(), name='sync_data'),
]
