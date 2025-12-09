import os
import django
import sys

# Add the project root to sys.path
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Project.settings')
django.setup()

from django.contrib.auth.models import User
from ChatRoom.models import UserProfile
from ChatRoom.serializers import UserSerializer

try:
    print("Attempting to create/get user...")
    user, created = User.objects.get_or_create(username="debug_user_final")
    print(f"User: {user}, Created: {created}")
    
    print("Attempting to create/get profile...")
    profile, p_created = UserProfile.objects.get_or_create(user=user)
    print(f"Profile: {profile}, Created: {p_created}")
    
    print("Attempting to serialize...")
    serializer = UserSerializer(user)
    print(f"Serialized data: {serializer.data}")
    
except Exception as e:
    print(f"CAUGHT EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
