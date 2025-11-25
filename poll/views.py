from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status
from .models import Poll, Option, Vote
from .serializers import PollSerializer


class PollListCreateView(generics.ListCreateAPIView):
    queryset = Poll.objects.all().order_by("-id")
    serializer_class = PollSerializer


class VoteView(APIView):
    def post(self, request, option_id):
        option = Option.objects.get(id=option_id)
        poll = option.poll

        # 🔥 Allow anonymous user by mapping to user ID = 1
        if request.user.is_authenticated:
            user = request.user
        else:
            # Get or create a default user for anonymous votes
            from django.contrib.auth.models import User
            user, _ = User.objects.get_or_create(username="guest_user", defaults={"password": "guest123"})

        # For single-choice polls → delete old vote
        if not poll.allow_multiple:
            Vote.objects.filter(user=user, option__poll=poll).delete()

        # Create vote
        vote, created = Vote.objects.get_or_create(user=user, option=option)

        return Response(
            {"message": "Vote recorded", "created": created},
            status=status.HTTP_200_OK
        )
