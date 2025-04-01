from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User, Group 

from django.http import HttpResponse

from google.cloud import vision

import cv2
import base64
import os



from .models import Cards
# Create your views here.

@login_required(login_url='/login')
def home(request):
    all_cards = Cards.objects.all()
    return render(request, 'Main/home.html', {'all': all_cards})


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
    


    # ---------------------------------------
# Webcam Capture + Google Cloud OCR
# ---------------------------------------
@login_required(login_url='/login')
def webcam_capture(request):
    if request.method == "POST":
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        cv2.destroyAllWindows()

        if not ret:
            return HttpResponse("Failed to capture image")

        # Encode the captured frame to JPEG buffer, then base64 encode it
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_image = base64.b64encode(buffer).decode()

        # Google Vision OCR call
        client = vision.ImageAnnotatorClient()
        image = vision.Image(content=base64.b64decode(encoded_image))
        response = client.text_detection(image=image)
        texts = response.text_annotations

        detected_text = texts[0].description if texts else "No text detected"

        return render(request, 'Main/webcam_result.html', {'text': detected_text})

    return render(request, 'Main/webcam.html')