"""
Meeting App Permissions
Custom permission classes for team and channel access control
"""

from rest_framework import permissions
from .models import TeamMembership, ChannelMembership, OrganizationMembership


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the organization
    """
    
    def has_object_permission(self, request, view, obj):
        # Get organization from object
        if hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            organization = obj
        
        return OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True
        ).exists()


class IsOrganizationAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin or owner of the organization
    """
    
    def has_object_permission(self, request, view, obj):
        # Get organization from object
        if hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            organization = obj
        
        membership = OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True
        ).first()
        
        return membership and membership.is_admin()


class IsOrganizationOwner(permissions.BasePermission):
    """
    Permission to check if user is the owner of the organization
    """
    
    def has_object_permission(self, request, view, obj):
        # Get organization from object
        if hasattr(obj, 'organization'):
            organization = obj.organization
        else:
            organization = obj
        
        membership = OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user,
            is_active=True,
            role='owner'
        ).first()
        
        return membership is not None


class IsTeamMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the team
    """
    
    def has_object_permission(self, request, view, obj):
        # Get team from object
        if hasattr(obj, 'team'):
            team = obj.team
        else:
            team = obj
        
        return TeamMembership.objects.filter(
            team=team,
            user=request.user,
            is_active=True
        ).exists()


class IsTeamAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin or owner of the team
    """
    
    def has_object_permission(self, request, view, obj):
        # Get team from object
        if hasattr(obj, 'team'):
            team = obj.team
        else:
            team = obj
        
        membership = TeamMembership.objects.filter(
            team=team,
            user=request.user,
            is_active=True
        ).first()
        
        return membership and membership.is_admin()


class IsChannelMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the channel
    """
    
    def has_object_permission(self, request, view, obj):
        # Get channel from object
        if hasattr(obj, 'channel'):
            channel = obj.channel
        else:
            channel = obj
        
        return ChannelMembership.objects.filter(
            channel=channel,
            user=request.user,
            is_active=True
        ).exists()


class CanManageChannel(permissions.BasePermission):
    """
    Permission to check if user can manage the channel
    """
    
    def has_object_permission(self, request, view, obj):
        # Get channel from object
        if hasattr(obj, 'channel'):
            channel = obj.channel
        else:
            channel = obj
        
        # Check if user is channel owner/moderator
        channel_membership = ChannelMembership.objects.filter(
            channel=channel,
            user=request.user,
            is_active=True,
            role__in=['owner', 'moderator']
        ).first()
        
        if channel_membership:
            return True
        
        # Or team admin
        team_membership = TeamMembership.objects.filter(
            team=channel.team,
            user=request.user,
            is_active=True
        ).first()
        
        return team_membership and team_membership.is_admin()
