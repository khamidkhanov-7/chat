from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.sender == request.user


class IsRoomMember(permissions.BasePermission):
    """
    Custom permission to only allow room members to access room content.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        # Check if user is a member of the room
        if hasattr(obj, 'room'):
            return obj.room.members.filter(id=request.user.id).exists()
        elif hasattr(obj, 'members'):
            return obj.members.filter(id=request.user.id).exists()
        return False