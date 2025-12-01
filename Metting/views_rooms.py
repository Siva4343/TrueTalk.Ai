# meet/views_rooms.py
import string
import random
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

def _short_room_id(length=7):
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))

@csrf_exempt
@require_POST
def create_room(request):
    """
    Minimal endpoint that returns a short random room id.
    Frontend calls POST /api/rooms/create/ to create & join.
    """
    room_id = _short_room_id(7)
    return JsonResponse({"room_id": room_id})
