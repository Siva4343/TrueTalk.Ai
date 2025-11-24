from django.http import HttpResponse

def index(request):
    return HttpResponse("Metting app is working")
