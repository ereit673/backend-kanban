from django.urls import path
from . import views

urlpatterns = [
    path('boards/', views.BoardList.as_view())
]
