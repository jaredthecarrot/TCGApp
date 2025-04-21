from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.http import JsonResponse
from .models import Card
import base64
from django.core.files.base import ContentFile
from .models import UploadedImage

from django.shortcuts import get_object_or_404, redirect

import base64
import uuid

from django.conf import settings

import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta
from .models import Card


# Create your views here.

def home(request):
    return render(request, 'Main/home.html')

@login_required(login_url='/login')
def catalog(request):
    query = request.GET.get('q', '')
    if query:
        cards = Card.objects.filter(
            Q(cleanName__icontains=query) |
            Q(extNumber__icontains=query) |
            Q(subTypeName__icontains=query)
        )
    else:
        cards = Card.objects.all()
    return render(request, 'Main/catalog.html', {'cards': cards})

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

@login_required(login_url='/login')
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
        save_flag  = request.POST.get("save")      # will be "true" when uploading
        chosen_id  = request.POST.get("card_id")   # the user’s selection

        if not image_data:
            return JsonResponse({"error": "No image data received"}, status=400)

        # decode the image
        fmt, imgstr = image_data.split(";base64,")
        ext = fmt.split("/")[-1]
        img_data = base64.b64decode(imgstr)
        image_file = ContentFile(img_data, name=f"{uuid.uuid4()}.{ext}")

        try:
            # OCR
            from google.cloud import vision
            client = vision.ImageAnnotatorClient()
            vision_image = vision.Image(content=img_data)
            resp = client.text_detection(image=vision_image)
            texts = resp.text_annotations
            detected = texts[0].description if texts else "No text detected"

            # find extNumber (allow optional single‐letter suffix)
            import re
            m = re.search(r'[A-Z]{2}\d{2}-\d{3}[A-Z]?', detected)
            variants = []
            if m:
                num = m.group().upper()
                # grab every card whose extNumber exactly matches
                cards = Card.objects.filter(extNumber=num)

                # Append every match—no more deduping by subtype
                for c in cards:
                    variants.append({
                        "id":           c.id,
                        "cleanName":    c.cleanName,
                        "subTypeName":  c.subTypeName,
                        "imageUrl":     c.imageUrl,
                        "marketPrice":  c.marketPrice,
                        "url":          c.url,
                    })
            # if this request is the “upload” pass, perform the save
            if save_flag == "true" and chosen_id:
                card_obj = get_object_or_404(Card, pk=chosen_id)
                UploadedImage.objects.create(
                    user=request.user,
                    image=image_file,
                    matched_card=card_obj
                )
                return JsonResponse({"success": True})

            # otherwise just return OCR + variants
            return JsonResponse({
                "text_result":     detected,
                "matching_cards":  variants
            })

        except Exception as e:
            print("OCR Error:", e)
            return JsonResponse({"error": "OCR failed"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required(login_url='/login')
def scanned_cards(request):
    q = request.GET.get('q', '').strip()
    qs = UploadedImage.objects.filter(user=request.user).select_related('matched_card')
    if q:
        qs = qs.filter(matched_card__cleanName__icontains=q)

    images_with_predictions = []
    for image in qs:
        matched_card = image.matched_card
        if matched_card:
            # Calculate predicted price dynamically
            prices = [matched_card.lowPrice, matched_card.midPrice, matched_card.highPrice, matched_card.marketPrice]
            predicted_price = round(sum(prices) / len(prices), 2)  # Round to 2 decimal places
            images_with_predictions.append({
                'image': image,
                'predictions': predicted_price
            })
        else:
            images_with_predictions.append({
                'image': image,
                'predictions': None
            })

    return render(request, 'Main/scanned_cards.html', {
        'images_with_predictions': images_with_predictions,
        'q': q,
    })

@login_required(login_url='/login')
def save_scanned_card(request):
    if request.method == "POST":
        image_data = request.POST.get("image_data")
        card_id = request.POST.get("card_id")

        if not image_data or not card_id:
            return JsonResponse({"error": "Missing data"}, status=400)

        try:
            # Decode and store image
            format, imgstr = image_data.split(";base64,")
            ext = format.split("/")[-1]
            img_data = base64.b64decode(imgstr)
            image_file = ContentFile(img_data, name=f"{uuid.uuid4()}.{ext}")

            matched_card = get_object_or_404(Card, id=card_id)

            UploadedImage.objects.create(
                image=image_file,
                matched_card=matched_card,
                user=request.user  # make sure your model includes this
            )

            return JsonResponse({"message": "Card saved successfully."})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid method"}, status=405)