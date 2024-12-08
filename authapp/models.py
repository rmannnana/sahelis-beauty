from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField
from django.core.validators import EmailValidator


# Gestionnaire personnalisé pour la création d'utilisateur
class UserManager(BaseUserManager):
    def create_user(self, phone, first_name, last_name, email, country, password=None):
        if not phone:
            raise ValueError("Le numéro de téléphone est requis")
        if not email:
            raise ValueError("L'email est requis")
        user = self.model(
            phone=phone,
            first_name=first_name,
            last_name=last_name,
            email=self.normalize_email(email),  # Normalisation de l'email
            country=country,
        )
        if password:
            user.set_password(password)  # Hachage sécurisé du mot de passe
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, first_name, last_name, email, country, password):
        user = self.create_user(phone, first_name, last_name, email, country, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(
        unique=True,
        validators=[
            EmailValidator(message="Veuillez entrer une adresse email valide.")
        ],
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
    )  # Email unique et validé
    country = CountryField()  # Pays de l'utilisateur
    phone = PhoneNumberField(unique=True)  # Numéro de téléphone unique
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name", "last_name", "email", "country"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    def set_password(self, raw_password):
        """Permet de hacher le mot de passe en cas de modification directe."""
        super().set_password(raw_password)
