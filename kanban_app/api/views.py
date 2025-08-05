from .serializers import BoardListSerializer, BoardDetailSerializer, BoardUpdateSerializer, UserMiniSerializer, TaskListSerializer
from kanban_app.models import Board, Task
from rest_framework import generics
from rest_framework.response import Response


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
