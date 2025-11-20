from django.urls import path
from .views import (
    JobListCreateView, JobDetailView,
    JobApplicationCreateView, JobApplicationListView
)

urlpatterns = [
    # Job
    path('jobs/', JobListCreateView.as_view()),
    path('jobs/<int:pk>/', JobDetailView.as_view()),

    # Job Applications
    path('jobs/apply/', JobApplicationCreateView.as_view()),
    path('jobs/applications/', JobApplicationListView.as_view()),
]
