from django.urls import path
from . import api_views

app_name = 'accounts_api'

urlpatterns = [
    path('me/', api_views.MeView.as_view(), name='me'),
    path('me/profile/', api_views.MyProfileView.as_view(), name='my_profile'),
]
