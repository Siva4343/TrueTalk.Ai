from rest_framework.generics import ListAPIView
from .models import Message
from .serializers import MessageSerializer

class MessageListAPI(ListAPIView):
    queryset = Message.objects.all().order_by("-timestamp")
    serializer_class = MessageSerializer
