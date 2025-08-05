from django.contrib.auth import get_user_model
from django.db.models import Q
from .permissions import IsOwnerOrMemberWithDeleteOwnerOnly
from .serializers import BoardListSerializer, BoardDetailSerializer, BoardUpdateSerializer, UserMiniSerializer, TaskListSerializer, TaskDetailSerializer, CommentListSerializer
from kanban_app.models import Board, Task, Comment
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

User = get_user_model()


class BoardListCreateView(generics.ListCreateAPIView):
    serializer_class = BoardListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Board.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrMemberWithDeleteOwnerOnly]
    http_method_names = ['get', 'patch', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def partial_update(self, request, *args, **kwargs):
        board = self.get_object()
        self.check_object_permissions(request, board)
        response = super().partial_update(request, *args, **kwargs)
        board.refresh_from_db()
        user_serializer = UserMiniSerializer(board.owner)
        members_serializer = UserMiniSerializer(board.members.all(), many=True)

        custom_response = {
            "id": board.id,
            "title": board.title,
            "owner_data": user_serializer.data,
            "members_data": members_serializer.data
        }

        return Response(custom_response)


class EmailCheckView(APIView):
    def get(self, request):
        email = request.query_params.get('email')

        if not email:
            return Response({'detail': 'Email parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Email nicht gefunden. Die Email existiert nicht.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user_data = UserMiniSerializer(user).data
        return Response(user_data)


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
