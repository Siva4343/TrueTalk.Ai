from django.contrib import admin
from .models import Job
from .models import JobApplication

admin.site.register(Job)
admin.site.register(JobApplication)
