from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Poll, PollOption, Vote
from .serializers import PollSerializer

class PollCreateView(generics.CreateAPIView):
    serializer_class = PollSerializer
    permission_classes = [IsAuthenticated]  # Require login

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PollListView(generics.ListAPIView):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer


class PollDetailView(generics.RetrieveAPIView):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer


class PollVoteView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, poll_id):
        poll = get_object_or_404(Poll, id=poll_id)
        option_id = request.data.get("option_id")

        option = get_object_or_404(PollOption, id=option_id, poll=poll)

        if not poll.allow_multiple:
            Vote.objects.filter(poll=poll, user=request.user).delete()

        existing_vote = Vote.objects.filter(poll=poll, option=option, user=request.user).first()

        if existing_vote:
            existing_vote.delete()
            return Response({"message": "Vote removed"})

        Vote.objects.create(poll=poll, option=option, user=request.user)
        return Response({"message": "Vote added"}, status=201)


  