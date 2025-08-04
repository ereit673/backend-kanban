from .serializers import BoardSerializer
from kanban_app.models import Board
from rest_framework import generics


class BoardList(generics.ListCreateAPIView):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
