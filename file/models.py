from django.db import models

def upload_to(instance, filename):
    if instance.file_type == "image":
        return f"uploads/images/{filename}"
    elif instance.file_type == "video":
        return f"uploads/videos/{filename}"
    elif instance.file_type == "document":
        return f"uploads/documents/{filename}"
    elif instance.file_type == "scan":
        return f"uploads/scans/{filename}"
    elif instance.file_type == "audio":   
        return f"uploads/audio/{filename}"
    return f"uploads/other/{filename}"
class SharedFile(models.Model):

    FILE_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("document", "Document"),
        ("scan", "Scan Document"),
        ("audio", "Audio"),  
    ]

    file_type = models.CharField(max_length=20, choices=FILE_TYPES)
    file = models.FileField(upload_to=upload_to)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file_type} - {self.file.name}" 




