from rest_framework import permissions


class IsCallParticipant(permissions.BasePermission):
    """
    Permission to check if user is a participant (caller or receiver) in the call
    """
    message = "You must be a participant in this call to perform this action."
    
    def has_object_permission(self, request, view, obj):
        # Check if user is either caller or receiver
        return request.user in [obj.caller, obj.receiver]


class IsCallReceiver(permissions.BasePermission):
    """
    Permission to check if user is the receiver of the call
    """
    message = "Only the call receiver can perform this action."
    
    def has_object_permission(self, request, view, obj):
        return request.user == obj.receiver


class IsCallCaller(permissions.BasePermission):
    """
    Permission to check if user is the caller
    """
    message = "Only the call initiator can perform this action."
    
    def has_object_permission(self, request, view, obj):
        return request.user == obj.caller


class CanEndCall(permissions.BasePermission):
    """
    Permission to check if user can end the call
    Both caller and receiver can end the call
    """
    message = "You don't have permission to end this call."
    
    def has_object_permission(self, request, view, obj):
        # Only participants can end a call
        is_participant = request.user in [obj.caller, obj.receiver]
        # Call must be active (initiated or ongoing)
        is_active = obj.status in ['initiated', 'ongoing']
        return is_participant and is_active


class IsAuthenticated(permissions.BasePermission):
    """
    Custom IsAuthenticated permission with better error message
    """
    message = "Authentication credentials were not provided or are invalid."
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
