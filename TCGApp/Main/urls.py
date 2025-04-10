from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('catalog', views.catalog, name='catalog'),
    path('image_capture', views.image_capture, name='image_capture'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('sign-up', views.sign_up, name='sign_up'),
    path('scanned_cards/', views.scanned_cards, name='scanned_cards'),
    path('delete_image/<int:image_id>/', views.delete_image, name='delete_image'),
    path('webcam/', views.webcam_capture, name='webcam_capture'),
]