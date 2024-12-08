from django import forms
from django.core.validators import RegexValidator
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from phonenumber_field.formfields import PhoneNumberField
from .models import User
from django.utils.safestring import mark_safe
import phonenumbers  # Bibliothèque pour valider et manipuler les numéros de téléphone


class CustomCountrySelectWidget(CountrySelectWidget):
    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        if value:
            country_code = str(value).lower()
            flag_span = f'<span class="flag-icon flag-icon-{country_code}" style="margin-right: 10px;"></span>'
            html = html.replace('>', f'>{flag_span}', 1)
        return mark_safe(html)


class UserRegistrationForm(forms.ModelForm):
    """Formulaire d'inscription pour les utilisateurs"""

    country = CountryField(blank_label="Choisissez un pays").formfield(
        widget=CustomCountrySelectWidget(attrs={"class": "form-select"})
    )
    phone = forms.CharField(
        widget=forms.TextInput(
            attrs={"placeholder": "Ex: 0123456789", "class": "form-control"}
        ),
        label="Numéro de téléphone",
        validators=[
            RegexValidator(
                regex=r"^\d{7,15}$",
                message="Veuillez entrer un numéro de téléphone valide sans l'indicatif du pays.",
            )
        ],
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Votre email"}
        ),
        label="Adresse email",
        help_text="Assurez-vous que l'email est valide.",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        min_length=8,
        help_text="Le mot de passe doit contenir au moins 8 caractères, une lettre et un chiffre.",
        label="Mot de passe",
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Confirmer le mot de passe",
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "country", "phone", "email", "password"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Votre prénom"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Votre nom"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get("phone")
        country = cleaned_data.get("country")
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        # Vérifier que les mots de passe correspondent
        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Les mots de passe ne correspondent pas.")

        # Ajouter l'indicatif téléphonique au numéro de téléphone
        if phone and country:
            try:
                # Valider le numéro avec l'indicatif
                parsed_phone = phonenumbers.parse(phone, region=str(country))
                if not phonenumbers.is_valid_number(parsed_phone):
                    raise phonenumbers.NumberParseException(
                        None, "Numéro de téléphone invalide"
                    )
                # Format complet du numéro
                cleaned_data["phone"] = phonenumbers.format_number(
                    parsed_phone, phonenumbers.PhoneNumberFormat.E164
                )
            except phonenumbers.NumberParseException:
                self.add_error(
                    "phone", "Le numéro de téléphone est invalide pour le pays sélectionné."
                )

        # Vérifier l'unicité de l'email
        if email and User.objects.filter(email=email).exists():
            self.add_error("email", "Un compte avec cet email existe déjà.")

        return cleaned_data

        

class UserLoginForm(forms.Form):
    """Formulaire de connexion pour les utilisateurs"""
    phone = PhoneNumberField(
        widget=forms.TextInput(attrs={'placeholder': 'Ex: +2250123456789', 'class': 'form-control'}),
        label="Numéro de téléphone"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Mot de passe"
    )


# Formulaires de réinitialisation de mot de passe
from django.contrib.auth.forms import SetPasswordForm as DjangoSetPasswordForm

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Votre email"}))


class SetPasswordForm(DjangoSetPasswordForm):
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Nouveau mot de passe"}),
    )
    new_password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirmez le mot de passe"}),
    )
