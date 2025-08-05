from django.urls import path
from . import views

urlpatterns = [
    path('boards/', views.BoardListCreateView.as_view()),
    path('boards/<int:pk>', views.BoardDetailView.as_view()),
    path('tasks/', views.TaskList.as_view()),
    path('tasks/assigned-to-me/', views.AssignedToMeTaskList.as_view()),
    path('tasks/reviewing/', views.ReviewingList.as_view()),
    path('tasks/<int:pk>', views.TaskDetail.as_view())
]
