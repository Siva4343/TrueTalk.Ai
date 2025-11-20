from rest_framework import generics
from job.models import Job, JobApplication
from job.serializers import JobSerializer, JobApplicationSerializer

# -------------------------------
# JOB CRUD
# -------------------------------

class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer


# -------------------------------
# APPLY TO JOB
# -------------------------------

class JobApplicationCreateView(generics.CreateAPIView):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer


class JobApplicationListView(generics.ListAPIView):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer

