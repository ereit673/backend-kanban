from django.urls import path
from . import views

urlpatterns = [
    path('boards/', views.BoardListCreateView.as_view()),
    path('boards/<int:pk>', views.BoardDetailView.as_view()),
    path('tasks/', views.TaskList.as_view())
]
