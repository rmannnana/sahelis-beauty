from django.urls import path
from django.contrib.auth import views as auth_views
from .views import auth_page, password_reset_request, password_reset_confirm

app_name = "authapp"

urlpatterns = [
    path('', auth_page, name='auth_page'),
    path('password-reset/', password_reset_request, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
]
