from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('predict/', views.salary_predictor, name='salary_predictor'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('my-market-position/', views.market_position, name='market_position'),
]
