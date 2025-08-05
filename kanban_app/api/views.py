from .serializers import BoardListSerializer, BoardDetailSerializer, BoardUpdateSerializer, UserMiniSerializer, TaskListSerializer, TaskDetailSerializer, CommentListSerializer
from kanban_app.models import Board, Task, Comment
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied


class BoardListCreateView(generics.ListCreateAPIView):
    queryset = Board.objects.all()
    serializer_class = BoardListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Board.objects.all()
    http_method_names = ['get', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        board = self.get_object()

        user_serializer = UserMiniSerializer(board.owner)
        members_serializer = UserMiniSerializer(board.members.all(), many=True)

        custom_response = {
            "id": board.id,
            "title": board.title,
            "owner_data": user_serializer.data,
            "members_data": members_serializer.data
        }

        return Response(custom_response)


class TaskList(generics.CreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskListSerializer


class AssignedToMeTaskList(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class ReviewingList(generics.ListAPIView):
    serializer_class = TaskListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user)


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskDetailSerializer
    queryset = Task.objects.all()
    http_method_names = ['patch', 'delete']


class CommentList(generics.ListCreateAPIView):
    serializer_class = CommentListSerializer

    def get_queryset(self):
        return Comment.objects.filter(task_id=self.kwargs['task_id'])

    def perform_create(self, serializer):
        task_id = self.kwargs['task_id']
        task = Task.objects.get(id=task_id)
        serializer.save(task=task, author=self.request.user)


class CommentDestroy(generics.DestroyAPIView):
    serializer_class = CommentListSerializer

    def get_queryset(self):
        return Comment.objects.filter(task_id=self.kwargs['task_id'])

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied(
                "Verboten. Nur der Ersteller des Kommentars darf ihn löschen.")
        instance.delete()
