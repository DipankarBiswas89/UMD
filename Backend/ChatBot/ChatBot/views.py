from django.http import HttpResponse

def home(request):
    return HttpResponse('Welcome to UMD!')

def login(request):
    return HttpResponse("This is my Login page")