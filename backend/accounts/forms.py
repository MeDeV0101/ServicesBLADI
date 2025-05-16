from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User

class UserEditForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Ancien mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True, 'class': 'form-control'}),
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )
    new_password2 = forms.CharField(
        label="Confirmation du nouveau mot de passe",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
    )
