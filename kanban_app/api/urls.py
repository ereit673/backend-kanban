from django.urls import path
from . import views

urlpatterns = [
    path('boards/', views.BoardListView.as_view()),
    path('boards/<int:pk>', views.BoardDetailView.as_view())
]
