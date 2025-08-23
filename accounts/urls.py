from django.urls import path
from . import views
from accounts.views import LogoutViewAllowGET
from .views import login_view, register_view, logout_view, dashboard_redirect

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard_redirect'),
]