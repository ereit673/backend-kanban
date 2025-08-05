from rest_framework.permissions import BasePermission


class IsOwnerOrMemberWithDeleteOwnerOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return obj.owner == request.user
        else:
            return request.user == obj.owner or request.user in obj.members.all()
