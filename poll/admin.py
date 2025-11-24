from django.contrib import admin
from .models import Poll, Choice, Vote

@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'created_by', 'created_at')
    search_fields = ('question', 'created_by__username')
    list_filter = ('created_at',)

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    # use the actual field name 'choice_text'
    list_display = ('id', 'choice_text', 'poll')
    search_fields = ('choice_text', 'poll__question')

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    # use actual Vote model fields (no session_key)
    list_display = ('id', 'poll', 'choice', 'voted_by', 'voted_at')
    search_fields = ('poll__question', 'choice__choice_text', 'voted_by__username')
    list_filter = ('voted_at',)

