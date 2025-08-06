from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('guest-login/', views.GuestLoginView.as_view(), name='guest-login'),
    path('email-check/', views.EmailCheckView.as_view(), name='email-check')
]
