from django.contrib.auth import get_user_model
from django.db.models import Q

from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from kanban_app.models import Board, Comment, Task

from .permissions import IsBoardMember, IsBoardMemberForComments, IsOwnerOrMemberWithDeleteOwnerOnly, IsTaskOwnerOrBoardOwner
from .serializers import (BoardDetailSerializer, BoardListSerializer, BoardUpdateSerializer,
                          CommentListSerializer, TaskDetailSerializer, TaskListSerializer, UserMiniSerializer)


User = get_user_model()


class BoardListCreateView(generics.ListCreateAPIView):
    """
    API view to list all boards where the authenticated user is either
    the owner or a member, and to allow creation of new boards.

    GET: Returns boards owned by or shared with the user.
    POST: Creates a new board.
    """
    serializer_class = BoardListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve boards where the user is owner or member.

        Returns:
            QuerySet: Boards related to the requesting user.
        """
        user = self.request.user
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()

    def get_serializer_context(self):
        """
        Provide extra context to serializer, including the request.

        Returns:
            dict: Context dictionary with request object.
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to retrieve, partially update, or delete a specific board.

    Permissions:
    - Authenticated users who are owner or members.
    - Only the owner can delete the board.

    GET: Retrieve board details.
    PATCH: Partially update board details.
    DELETE: Delete board if requester is the owner.
    """
    queryset = Board.objects.all()
    permission_classes = [IsAuthenticated, IsOwnerOrMemberWithDeleteOwnerOnly]
    http_method_names = ['get', 'patch', 'delete']

    def get_serializer_class(self):
        """
        Returns serializer class depending on HTTP method.
        PATCH requests use BoardUpdateSerializer; others use BoardDetailSerializer.

        Returns:
            Serializer class
        """
        if self.request.method == 'PATCH':
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def partial_update(self, request, *args, **kwargs):
        """
        Handle partial update of a board instance after permission check.

        Returns:
            Response: Custom serialized board data after update.
        """
        board = self.get_object()
        self.check_object_permissions(request, board)
        response = super().partial_update(request, *args, **kwargs)
        board.refresh_from_db()
        return Response(self.build_custom_response(board))

    def build_custom_response(self, board):
        """
        Construct a custom response dictionary for the board.

        Args:
            board (Board): Board instance to serialize.

        Returns:
            dict: Custom board representation including owner and members data.
        """
        return {
            "id": board.id,
            "title": board.title,
            "owner_data": UserMiniSerializer(board.owner).data,
            "members_data": UserMiniSerializer(board.members.all(), many=True).data,
        }


class TaskList(generics.CreateAPIView):
    """
    API view to create a new task in a board.

    POST: Create a task, only if user is board owner or member.
    """
    queryset = Task.objects.all()
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        """
        Override to check user permissions before saving the task.

        Args:
            serializer: Serializer with validated data.

        Raises:
            NotFound: If the referenced board does not exist.
            PermissionDenied: If user cannot create tasks on the board.
        """
        board = serializer.validated_data.get('board')
        self.check_user_can_create_task(board)
        serializer.save(owner=self.request.user)

    def check_user_can_create_task(self, board):
        """
        Check if the user is allowed to create tasks on the specified board.

        Args:
            board (Board): Board instance to check against.

        Raises:
            NotFound: If board does not exist.
            PermissionDenied: If user is neither owner nor member of the board.
        """
        if not Board.objects.filter(id=board.id).exists():
            raise NotFound("Board not found")

        user = self.request.user
        if user != board.owner and user not in board.members.all():
            raise PermissionDenied(
                "You are not allowed to create tasks for this board.")


class AssignedToMeTaskList(generics.ListAPIView):
    """
    API view to list tasks assigned to the authenticated user.

    GET: Return tasks where the authenticated user is the assignee.
    """
    serializer_class = TaskListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return queryset of tasks assigned to the user.

        Returns:
            QuerySet: Tasks assigned to request.user.
        """
        return Task.objects.filter(assignee=self.request.user)


class ReviewingList(generics.ListAPIView):
    """
    API view to list tasks assigned to the authenticated user as reviewer.

    GET: Return tasks where the authenticated user is the reviewer.
    """
    serializer_class = TaskListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return queryset of tasks where user is the reviewer.

        Returns:
            QuerySet: Tasks assigned to the user as reviewer.
        """
        return Task.objects.filter(reviewer=self.request.user)


class TaskDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    API view to partially update or delete a task.

    PATCH: Partial update (except board field).
    DELETE: Delete the task.

    Permissions:
    - User must be a board member.
    - User must be task owner or board owner.
    """
    serializer_class = TaskDetailSerializer
    queryset = Task.objects.all()
    http_method_names = ['patch', 'delete']
    permission_classes = [IsBoardMember,
                          IsAuthenticated, IsTaskOwnerOrBoardOwner]

    def partial_update(self, request, *args, **kwargs):
        """
        Prevent modification of the 'board' field during partial update.

        Returns:
            Response: Error if 'board' is in data, otherwise standard partial update.
        """
        if 'board' in request.data:
            return Response(
                {"detail": "Modification of the board is not allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().partial_update(request, *args, **kwargs)


class CommentList(generics.ListCreateAPIView):
    """
    API view to list all comments for a task and create new comments.

    GET: List comments for a task.
    POST: Create a comment for a task by the authenticated user.

    Permissions:
    - User must be a member of the board the task belongs to.
    """
    serializer_class = CommentListSerializer
    permission_classes = [IsBoardMemberForComments, IsAuthenticated]

    def get_queryset(self):
        """
        Return all comments related to the specified task.

        Returns:
            QuerySet: Comments filtered by task_id from URL kwargs.
        """
        return Comment.objects.filter(task_id=self.kwargs['task_id'])

    def perform_create(self, serializer):
        """
        Create a new comment linked to the task and authored by the user.

        Args:
            serializer: Serializer with validated data.
        """
        task = self.get_task_or_404()
        serializer.save(task=task, author=self.request.user)

    def get_task_or_404(self):
        """
        Retrieve the task for the given task_id or raise 404 if not found.

        Returns:
            Task instance
        """
        try:
            return Task.objects.get(id=self.kwargs['task_id'])
        except Task.DoesNotExist:
            raise NotFound("Task not found.")


class CommentDestroy(generics.DestroyAPIView):
    """
    API view to delete a comment.

    DELETE: Deletes a comment if the requester is the author.
    """
    serializer_class = CommentListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return queryset of comments filtered by task_id in URL kwargs.

        Returns:
            QuerySet: Comments for a specific task.
        """
        return Comment.objects.filter(task_id=self.kwargs['task_id'])

    def perform_destroy(self, instance):
        """
        Delete the comment if the requester is the author.

        Args:
            instance (Comment): Comment instance to delete.

        Raises:
            PermissionDenied: If the requester is not the author.
        """
        if instance.author != self.request.user:
            raise PermissionDenied()
        instance.delete()
