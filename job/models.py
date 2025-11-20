from django.db import models
from django.contrib.auth.models import User  # <-- Link application to real user

class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    posted_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    employment_type = models.CharField(
        max_length=50,
        choices=[
            ('FT', 'Full-Time'),
            ('PT', 'Part-Time'),
            ('CT', 'Contract'),
            ('IN', 'Internship'),
            ('TM', 'Temporary'),
        ],
        default='FT'
    )
    experience_level = models.CharField(
        max_length=50,
        choices=[
            ('EN', 'Entry Level'),
            ('MI', 'Mid Level'),
            ('SE', 'Senior Level'),
            ('EX', 'Executive'),
        ],
        default='EN'
    )

    def __str__(self):
        return f"{self.title} at {self.company}"


class JobApplication(models.Model):

    job = models.ForeignKey(Job, related_name="applications", on_delete=models.CASCADE)

    user = models.ForeignKey(User, related_name="applications", on_delete=models.CASCADE)

    cover_letter = models.TextField(null=True, blank=True)

    resume = models.FileField(upload_to="resumes/")

    applied_date = models.DateTimeField(auto_now_add=True)

    # New fields you can add

    phone = models.CharField(max_length=15, null=True, blank=True)        # Extra

    experience_years = models.IntegerField(null=True, blank=True)         # Extra

    expected_salary = models.IntegerField(null=True, blank=True)          # Extra

    portfolio_link = models.URLField(null=True, blank=True)               # Extra

    linkedin_profile = models.URLField(null=True, blank=True)             # Extra

    status = models.CharField(

        max_length=50,

        choices=[

            ('PENDING', 'Pending'),

            ('REVIEWED', 'Reviewed'),

            ('REJECTED', 'Rejected'),

            ('SELECTED', 'Selected'),

        ],

        default='PENDING'

    )
 
    notes = models.TextField(null=True, blank=True)  # HR/admin notes (optional)
 
    def __str__(self):

        return f"{self.user.username} applied for {self.job.title}"

 