from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User, Group
from django.http import JsonResponse
from .models import Card
import base64
from django.core.files.base import ContentFile
from .models import UploadedImage
# Create your views here.

@login_required(login_url='/login')
def home(request):
    return render(request, 'Main/home.html')

@login_required(login_url='/login')
def catalog(request):
    cards = Card.objects.all()
    return render(request, 'Main/catalog.html', {'cards': cards})

def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('/home')
    else:
        form = RegisterForm()

    return render(request, 'registration/sign_up.html', {"form": form})

def image_capture(request):
    return render(request, 'Main/image_capture.html')

def upload_image(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        image_data = data.get("image")
        if image_data:
            format, imgstr = image_data.split(';base64,')
            ext = format.split('/')[-1]
            image_file = ContentFile(base64.b64decode(imgstr), name=f"capture.{ext}")
            uploaded_image = UploadedImage.objects.create(image=image_file)
            return JsonResponse({"message": "Image uploaded successfully", "image_url": uploaded_image.image.url})
    return JsonResponse({"error": "Invalid request"}, status=400)  # Return proper error response

def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision

    client = vision.ImageAnnotatorClient()

    with open(path, "rb") as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    print("Texts:")

    for text in texts:
        print(f'\n"{text.description}"')

        vertices = [
            f"({vertex.x},{vertex.y})" for vertex in text.bounding_poly.vertices
        ]

        print("bounds: {}".format(",".join(vertices)))

    if response.error.message:
        raise Exception(
            "{}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors".format(response.error.message)
        )