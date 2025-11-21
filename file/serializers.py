from rest_framework import serializers
from .models import SharedFile

class SharedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharedFile
        fields = '__all__'


