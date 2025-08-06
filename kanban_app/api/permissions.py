from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from ..models import Task


class IsOwnerOrMemberWithDeleteOwnerOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return obj.owner == request.user
        else:
            return request.user == obj.owner or request.user in obj.members.all()


class IsBoardMember(BasePermission):
    def has_object_permission(self, request, view, obj):
        board = obj.board
        user = request.user

        if user in board.members.all():
            return True

        raise PermissionDenied(
            "You do not have permission to modify this task.")


class IsTaskOwnerOrBoardOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return request.user == obj.owner or request.user == obj.board.owner
        return True


class IsBoardMemberForComments(BasePermission):
    def has_permission(self, request, view):
        task_id = view.kwargs.get('task_id')
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return False

        user = request.user
        board = task.board

        return user == board.owner or user in board.members.all()
