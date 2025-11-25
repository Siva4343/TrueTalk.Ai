from django.urls import path
from .views import PollCreateView, PollListView, PollDetailView, PollVoteView

urlpatterns = [
    path('create/', PollCreateView.as_view(), name='poll-create'),
    path('', PollListView.as_view(), name='poll-list'),
    path('<int:pk>/', PollDetailView.as_view(), name='poll-detail'),
    path('<int:poll_id>/vote/', PollVoteView.as_view(), name='poll-vote'),
]


