from .serializers import BoardListSerializer, BoardDetailSerializer
from kanban_app.models import Board
from rest_framework import generics


class BoardListView(generics.ListCreateAPIView):
    queryset = Board.objects.all()
    serializer_class = BoardListSerializer


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Board.objects.all()
    serializer_class = BoardDetailSerializer
