from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.authentication import BaseAuthentication
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import Message
from .serializers import MessageSerializer


@method_decorator(csrf_exempt, name='dispatch')
class MessageListCreateView(generics.ListCreateAPIView):
    queryset = Message.objects.select_related("sender", "receiver").all()
    serializer_class = MessageSerializer
    permission_classes = [AllowAny]
    # No auth/CSRF for this demo API
    authentication_classes: list[BaseAuthentication] = []

    def perform_create(self, serializer):
        """
        The serializer's create() method now handles username conversion,
        so we can just save directly.
        """
        serializer.save()