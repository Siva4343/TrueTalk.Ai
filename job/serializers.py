from rest_framework import serializers
from job.models import Job, JobApplication

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'


class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'user', 'cover_letter', 'resume', 
            'applied_date', 'phone', 'experience_years', 
            'expected_salary', 'portfolio_link', 'linkedin_profile', 
            'status', 'notes', 'job_title', 'company_name'
        ]
        read_only_fields = ['user', 'applied_date', 'status', 'notes']