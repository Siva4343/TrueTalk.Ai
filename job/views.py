from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from job.models import Job, JobApplication
from job.serializers import JobSerializer, JobApplicationSerializer

# -------------------------------
# JOB CRUD
# -------------------------------

class JobListCreateView(generics.ListCreateAPIView):
    queryset = Job.objects.filter(is_active=True)
    serializer_class = JobSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer


# -------------------------------
# APPLY TO JOB
# -------------------------------

class JobApplicationCreateView(generics.CreateAPIView):
    queryset = JobApplication.objects.all()
    serializer_class = JobApplicationSerializer

    def create(self, request, *args, **kwargs):
        print("Received application data:", request.data)  # Debug print
        print("Received files:", request.FILES)  # Debug print
        
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Get or create a default user for testing
                # In production, you would use request.user
                default_user, created = User.objects.get_or_create(
                    username='default_applicant',
                    defaults={
                        'email': 'applicant@example.com',
                        'first_name': 'Default',
                        'last_name': 'Applicant'
                    }
                )
                
                # Save the application with the default user
                application = serializer.save(user=default_user)
                print("Application saved successfully:", application.id)
                
                return Response(
                    {
                        'message': 'Application submitted successfully!',
                        'application_id': application.id,
                        'data': JobApplicationSerializer(application).data
                    },
                    status=status.HTTP_201_CREATED
                )
                
            except Exception as e:
                print("Error saving application:", str(e))
                return Response(
                    {'error': f'Failed to save application: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            print("Serializer errors:", serializer.errors)
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )


class JobApplicationListView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer

    def get_queryset(self):
        # Return applications with related job data
        return JobApplication.objects.select_related('job').all()