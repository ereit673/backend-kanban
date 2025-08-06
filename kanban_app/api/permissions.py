from rest_framework.permissions import BasePermission
from ..models import Task


class IsOwnerOrMemberWithDeleteOwnerOnly(BasePermission):
    """
    Permission class that allows:
    - Only the owner of the object to DELETE it.
    - The owner or any member of the object to perform other actions.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the requesting user has permission on the object.

        Args:
            request: The HTTP request instance.
            view: The view being accessed.
            obj: The object being accessed.

        Returns:
            bool: True if permission is granted, False otherwise.
        """
        if request.method == 'DELETE':
            return obj.owner == request.user
        else:
            return request.user == obj.owner or request.user in obj.members.all()


class IsBoardMember(BasePermission):
    """
    Permission class that allows access only to users who are members of the board
    related to the object.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the requesting user is a member of the board of the object.

        Args:
            request: The HTTP request instance.
            view: The view being accessed.
            obj: The object being accessed (should have a 'board' attribute).

        Returns:
            bool: True if the user is a member of the board, False otherwise.
        """
        board = obj.board
        user = request.user
        return user in board.members.all()


class IsTaskOwnerOrBoardOwner(BasePermission):
    """
    Permission class that allows:
    - Only the task owner or the board owner to DELETE the task.
    - Allows all other actions by any user.
    """

    def has_object_permission(self, request, view, obj):
        """
        Check if the requesting user has permission on the task.

        Args:
            request: The HTTP request instance.
            view: The view being accessed.
            obj: The task object.

        Returns:
            bool: True if permission is granted, False otherwise.
        """
        if request.method == 'DELETE':
            return request.user == obj.owner or request.user == obj.board.owner
        return True


class IsBoardMemberForComments(BasePermission):
    """
    Permission class that grants access only if the requesting user
    is the owner or a member of the board associated with the task for which
    comments are being accessed or created.
    """

    def has_permission(self, request, view):
        """
        Check if the user has permission based on membership of the board.

        Args:
            request: The HTTP request instance.
            view: The view being accessed.

        Returns:
            bool: True if user is board owner or member, False otherwise.
        """
        task = self.get_task(view)
        if not task:
            return False

        user = request.user
        board = task.board
        return user == board.owner or user in board.members.all()

    def get_task(self, view):
        """
        Helper method to retrieve the Task object based on 'task_id' in URL kwargs.

        Args:
            view: The view instance, expected to have kwargs with 'task_id'.

        Returns:
            Task instance if found, else None.
        """
        task_id = view.kwargs.get('task_id')
        try:
            return Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return None
