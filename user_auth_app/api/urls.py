from django.urls import path

from . import views


urlpatterns = [
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('email-check/', views.EmailCheckView.as_view(), name='email-check')
]
