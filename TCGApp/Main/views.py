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

from django.shortcuts import get_object_or_404, redirect

from google.cloud import vision

import pandas as pd

import cv2
import base64
import os
import uuid

from django.conf import settings


# Create your views here.

@login_required(login_url='/login')
def home(request):
    return render(request, 'Main/home.html')

@login_required(login_url='/login')
def catalog(request):
    cards = Card.objects.all()
    return render(request, 'Main/catalog.html', {'cards': cards})

@login_required(login_url='/login')
def scanned_cards(request):
    images = UploadedImage.objects.all()  # Fetch all uploaded images from the database
    return render(request, 'Main/scanned_cards.html', {'images': images})

@login_required(login_url='/login')
def delete_image(request, image_id):
    image = get_object_or_404(UploadedImage, id=image_id)  # Get the image object by ID
    image.delete()  # Delete the image from the database
    return redirect('scanned_cards')  # Redirect back to the scanned cards page


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


@login_required(login_url='/login')
def webcam_capture(request):
    if request.method == "POST":
        image_data = request.POST.get("image_data")
        if not image_data:
            return JsonResponse({"error": "No image data received"}, status=400)

        # Decode Base64 image
        format, imgstr = image_data.split(";base64,")
        img_data = base64.b64decode(imgstr)
        filename = f"card_{uuid.uuid4().hex}.png"
        save_dir = os.path.join(settings.BASE_DIR, 'Main', 'static', 'captured_images')

        # Ensure directory exists
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        save_path = os.path.join(save_dir, filename)
        with open(save_path, "wb") as f:
            f.write(img_data)

        # OCR (Google Cloud Vision)
        credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        detected_text = "OCR skipped – no credentials found."
        card_price = None

        if credentials_path and os.path.exists(credentials_path):
            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=img_data)
            response = client.text_detection(image=image)
            texts = response.text_annotations
            detected_text = texts[0].description if texts else "No text detected"
            print(f"OCR Detected Text: {detected_text}")  # Log the detected text

            # Extract card number
            import re
            card_number_match = re.search(r'[A-Z]{2}\d{2}-\d{3}', detected_text)  # Match alphanumeric strings with hyphens
            if card_number_match:
                card_number = card_number_match.group().strip().upper()  # Normalize the card number
                print(f"Extracted Card Number: {card_number}")  # Log the extracted card number

                # Search the database for the card
                cards = Card.objects.filter(extNumber=card_number)
                if cards.exists():
                    card_price = cards.first().marketPrice  # Use the first matching card's price
                    print(f"Card Found: {cards.first().cleanName}, Price: {card_price}")  # Log the card details
                else:
                    card_price = "Card not found in the database."
                    print("No matching card found in the database.")
            else:
                card_price = "No valid card number found in the scanned text."
                print("No valid card number found in the scanned text.")

        return JsonResponse({
            "image_url": f"/static/captured_images/{filename}",
            "text_result": detected_text,
            "card_price": card_price
        })

    return render(request, 'Main/image_capture.html')