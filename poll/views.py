from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Poll, Choice, Vote
from .serializers import PollSerializer, ChoiceSerializer, VoteSerializer

class PollViewSet(viewsets.ModelViewSet):
    queryset = Poll.objects.all()
    serializer_class = PollSerializer
    
    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        poll = self.get_object()
        choice_id = request.data.get('choice')
        
        try:
            choice = Choice.objects.get(id=choice_id, poll=poll)
            vote, created = Vote.objects.get_or_create(
                poll=poll,
                voted_by=request.user,
                defaults={'choice': choice}
            )
            
            if not created:
                vote.choice = choice
                vote.save()
            
            return Response({'status': 'vote recorded'})
        except Choice.DoesNotExist:
            return Response(
                {'error': 'Invalid choice'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class ChoiceViewSet(viewsets.ModelViewSet):
    queryset = Choice.objects.all()
    serializer_class = ChoiceSerializer

class VoteViewSet(viewsets.ModelViewSet):
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
  