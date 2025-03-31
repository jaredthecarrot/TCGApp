from django.db import models

# Create your models here.

class Cards(models.Model):
    productId = models.CharField(("productId"), max_length=256)
    cleanName = models.CharField(("cleanname"), max_length=256)
    imageUrl = models.CharField(("imageUrl"), max_length=256)
    url = models.CharField(("url"), max_length=256)
    lowPrice = models.FloatField(("lowPrice"), )
    midPrice = models.FloatField(("midPrice"), )
    highPrice = models.FloatField(("highPrice"), )
    marketPrice = models.FloatField(("marketPrice"), )
    subTypeName = models.CharField(("subTypeName"), max_length=256)
    extNumber = models.CharField(("extNumber"), max_length=256)
    #extDescription = models.CharField(("extDescription"), max_length=1024)