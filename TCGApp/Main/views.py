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

import base64
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
        should_save = request.POST.get("save", None)

        if not image_data:
            return JsonResponse({"error": "No image data received"}, status=400)

        # Decode Base64 image
        format, imgstr = image_data.split(";base64,")
        ext = format.split("/")[-1]
        img_data = base64.b64decode(imgstr)
        image_name = f"{uuid.uuid4()}.{ext}"
        image_file = ContentFile(img_data, name=image_name)

        try:
            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=img_data)
            response = client.text_detection(image=image)
            texts = response.text_annotations
            detected_text = texts[0].description if texts else "No text detected"
            import re
            # Match card number (e.g., OP01-123)
            card_number_match = re.search(r'[A-Z]{2}\d{2}-\d{3}', detected_text)
            matched_card = None
            matching_cards = []

            if card_number_match:
                card_number = card_number_match.group().strip().upper()
                cards = Card.objects.filter(extNumber=card_number)

                seen_subtypes = set()
                for card in cards:
                    # Avoid duplicates for Normal and Foil
                    if card.subTypeName not in seen_subtypes:
                        seen_subtypes.add(card.subTypeName)
                        matching_cards.append({
                            'productId': card.productId,
                            'cleanName': card.cleanName,
                            'imageUrl': card.imageUrl,
                            'url': card.url,
                            'lowPrice': card.lowPrice,
                            'midPrice': card.midPrice,
                            'highPrice': card.highPrice,
                            'marketPrice': card.marketPrice,
                            'subTypeName': card.subTypeName,
                            'extNumber': card.extNumber,
                            'extDescription': card.extDescription,
                        })

                if cards.exists():
                    matched_card = cards.first()

            # Only save if 'save' is in POST
            if should_save:
                UploadedImage.objects.create(
                    image=image_file,
                    matched_card=matched_card,
                    user=request.user
                )

            return JsonResponse({
                "text_result": detected_text,
                "matching_cards": matching_cards
            })

        except Exception as e:
            print(f"OCR Error: {e}")
            return JsonResponse({"error": "OCR failed"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@login_required(login_url='/login')
def scanned_cards(request):
    images = UploadedImage.objects.filter(user=request.user).select_related('matched_card')
    return render(request, 'Main/scanned_cards.html', {'images': images}
    )

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
