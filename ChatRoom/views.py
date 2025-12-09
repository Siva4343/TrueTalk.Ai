from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.db.models import Q
from .models import Message, Group, UserProfile
from .serializers import MessageSerializer, GroupSerializer, UserSerializer
from django.contrib.auth.models import User


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    @action(detail=False, methods=['delete'])
    def delete_conversation(self, request):
        other_username = request.query_params.get('other_username')
        group_id = request.query_params.get('group_id')
        current_username = request.query_params.get('username')

        if not current_username:
             return Response({"error": "Current username is required"}, status=status.HTTP_400_BAD_REQUEST)

        if group_id:
            try:
                group = Group.objects.get(id=group_id)
                group.delete()
                return Response({"message": "Group deleted"}, status=status.HTTP_200_OK)
            except Group.DoesNotExist:
                return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        if other_username:
            messages = Message.objects.filter(
                (Q(sender__username=current_username) & Q(receiver__username=other_username)) |
                (Q(sender__username=other_username) & Q(receiver__username=current_username))
            )
            count, _ = messages.delete()
            return Response({"message": f"Deleted {count} messages"}, status=status.HTTP_200_OK)

        return Response({"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        group = self.get_object()
        username = request.data.get('username')
        
        if not username:
            return Response({"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            user = User.objects.get(username=username)
            group.members.add(user)
            return Response(GroupSerializer(group).data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        try:
            username = request.data.get("username")
            first_name = request.data.get("first_name")
            phone_number = request.data.get("phone_number")

            if not username:
                return Response(
                    {"error": "Username is required"}, status=status.HTTP_400_BAD_REQUEST
                )
            
            user, created = User.objects.get_or_create(username=username)
            
            if first_name:
                user.first_name = first_name
                user.save()
                
            if phone_number:
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.phone_number = phone_number
                profile.save()

            serializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        except Exception as e:
            import traceback
            return Response({"error": str(e), "traceback": traceback.format_exc()}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)