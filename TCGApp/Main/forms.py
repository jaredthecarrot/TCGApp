from django import forms
from .models import Cards
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

class CardForm(forms.ModelForm):
    class Meta:
        model = Cards
        fields = "__all__"