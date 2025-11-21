from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth.models import User

from .models import Message
from .serializers import MessageSerializer


class MessageListCreateView(generics.ListCreateAPIView):
    queryset = Message.objects.select_related("sender", "receiver").all()
    serializer_class = MessageSerializer
    permission_classes = [AllowAny]
    # No auth/CSRF for this demo API
    authentication_classes: list[BaseAuthentication] = []

    def perform_create(self, serializer):
        """
        Use the usernames sent by the client to get/create User objects,
        then save the Message. We also remove the helper fields from
        validated_data so they are NOT passed into Message.objects.create().
        """
        validated = dict(serializer.validated_data)

        # Take out helper fields so they don't go into Message.objects.create
        sender_username = validated.pop("sender_username", None)
        receiver_username = validated.pop("receiver_username", None)

        if not sender_username:
            raise ValueError("sender_username is required")

        sender, _ = User.objects.get_or_create(
            username=sender_username,
            defaults={"email": f"{sender_username}@example.com"},
        )

        receiver = None
        if receiver_username:
            receiver, _ = User.objects.get_or_create(
                username=receiver_username,
                defaults={"email": f"{receiver_username}@example.com"},
            )

        # Save message without the extra username fields
        serializer.save(sender=sender, receiver=receiver)