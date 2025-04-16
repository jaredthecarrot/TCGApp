from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Card(models.Model):
    productId = models.CharField(("productId"), max_length=256)
    cleanName = models.CharField(("cleanname"), max_length=256)
    imageUrl = models.URLField(("imageUrl"), max_length=256)
    url = models.URLField(("url"), max_length=256)
    lowPrice = models.FloatField(("lowPrice"), )
    midPrice = models.FloatField(("midPrice"), )
    highPrice = models.FloatField(("highPrice"), )
    marketPrice = models.FloatField(("marketPrice"), )
    subTypeName = models.CharField(("subTypeName"), max_length=256)
    extNumber = models.CharField(("extNumber"), max_length=256)
    extDescription = models.CharField(("extDescription"), max_length=1024)

    def __str__(self):
        return 'Name: ' + self.cleanName + ' - extNumber: ' + self.extNumber

class UploadedImage(models.Model):
    image = models.ImageField(upload_to="uploads/")
    created_at = models.DateTimeField(auto_now_add=True)
    matched_card = models.ForeignKey(Card, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_images', null=True, blank=True)