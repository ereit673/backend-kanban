from django.contrib.auth import get_user_model
from django.db.models import Q
from .permissions import IsOwnerOrMemberWithDeleteOwnerOnly, IsBoardMember, IsTaskOwnerOrBoardOwner, IsBoardMemberForComments
from .serializers import BoardListSerializer, BoardDetailSerializer, BoardUpdateSerializer, UserMiniSerializer, TaskListSerializer, TaskDetailSerializer, CommentListSerializer
from kanban_app.models import Board, Task, Comment
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
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
        return Response(self.build_custom_response(board))

    def build_custom_response(self, board):
        return {
            "id": board.id,
            "title": board.title,
            "owner_data": UserMiniSerializer(board.owner).data,
            "members_data": UserMiniSerializer(board.members.all(), many=True).data,
        }


class TaskList(generics.CreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        board = serializer.validated_data.get('board')
        self.check_user_can_create_task(board)
        serializer.save(owner=self.request.user)

    def check_user_can_create_task(self, board):
        if not Board.objects.filter(id=board.id).exists():
            raise NotFound("Board not found")

        user = self.request.user
        if user != board.owner and user not in board.members.all():
            raise PermissionDenied(
                "You are not allowed to create tasks for this board.")


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
    permission_classes = [IsBoardMember,
                          IsAuthenticated, IsTaskOwnerOrBoardOwner]

    def partial_update(self, request, *args, **kwargs):
        if 'board' in request.data:
            return Response(
                {"detail": "Modification of the board is not allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().partial_update(request, *args, **kwargs)


class CommentList(generics.ListCreateAPIView):
    serializer_class = CommentListSerializer
    permission_classes = [IsBoardMemberForComments, IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(task_id=self.kwargs['task_id'])

    def perform_create(self, serializer):
        task = self.get_task_or_404()
        serializer.save(task=task, author=self.request.user)

    def get_task_or_404(self):
        try:
            return Task.objects.get(id=self.kwargs['task_id'])
        except Task.DoesNotExist:
            raise NotFound("Task not found.")


class CommentDestroy(generics.DestroyAPIView):
    serializer_class = CommentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(task_id=self.kwargs['task_id'])

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied()
        instance.delete()
