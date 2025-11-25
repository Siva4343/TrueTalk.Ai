from rest_framework import serializers
from .models import Poll, PollOption

class PollOptionSerializer(serializers.ModelSerializer):
    vote_count = serializers.IntegerField(source='votes.count', read_only=True)

    class Meta:
        model = PollOption
        fields = ['id', 'text', 'vote_count']


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True)

    class Meta:
        model = Poll
        fields = ['id', 'question', 'allow_multiple', 'created_by', 'created_at', 'options']

    def create(self, validated_data):
        options = validated_data.pop('options')
        poll = Poll.objects.create(**validated_data)
        for opt in options:
            PollOption.objects.create(poll=poll, **opt)
        return poll

