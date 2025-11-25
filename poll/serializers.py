from rest_framework import serializers
from .models import Poll, Option, Vote

class OptionSerializer(serializers.ModelSerializer):
    votes = serializers.IntegerField(source="votes.count", read_only=True)
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = Option
        fields = ["id", "text", "votes", "percentage"]

    def get_percentage(self, obj):
        total_votes = Vote.objects.filter(option__poll=obj.poll).count()
        if total_votes == 0:
            return 0
        return round((obj.votes.count() / total_votes) * 100)


class PollSerializer(serializers.ModelSerializer):
    # Accept a list of strings from frontend
    options = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )

    # Return options with votes
    results = OptionSerializer(many=True, read_only=True, source="options")
    total_votes = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = ["id", "question", "allow_multiple", "options", "results", "total_votes"]

    def get_total_votes(self, obj):
        return Vote.objects.filter(option__poll=obj).count()

    def create(self, validated_data):
        option_texts = validated_data.pop("options")
        poll = Poll.objects.create(**validated_data)

        for text in option_texts:
            Option.objects.create(poll=poll, text=text)

        return poll
