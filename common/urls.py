"""
公共模块URL配置
"""
from django.urls import path
from .views import HealthCheckView

app_name = 'common'

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
]

