from django.urls import path
from .views import PollListCreateView, VoteView

urlpatterns = [
    path("polls/", PollListCreateView.as_view(), name="poll-list"),
    path("vote/<int:option_id>/", VoteView.as_view(), name="vote"),
]