from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from .forms import UserRegistrationForm, UserLoginForm, PasswordResetRequestForm, SetPasswordForm
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponse
from django.template.loader import render_to_string
from phonenumbers import parse, is_valid_number, NumberParseException, format_number, PhoneNumberFormat

def auth_page(request):
    if request.method == "POST":
        if "register" in request.POST:
            register_form = UserRegistrationForm(request.POST)
            login_form = UserLoginForm()
            if register_form.is_valid():
                user = register_form.save(commit=False)  # Ne pas encore sauvegarder en base
                country_code = str(register_form.cleaned_data["country"])  # Code pays (ex : "FR")
                local_phone = register_form.cleaned_data["phone"]  # Numéro local
                
                try:
                    # Construire et valider le numéro complet
                    parsed_phone = parse(local_phone, country_code)
                    if not is_valid_number(parsed_phone):
                        raise NumberParseException(0, "Numéro invalide.")
                    
                    # Format E.164 pour l'enregistrement (ex : "+33612345678")
                    user.phone = format_number(parsed_phone, PhoneNumberFormat.E164)
                except NumberParseException:
                    # Gérer l'erreur si le numéro est invalide
                    register_form.add_error("phone", "Numéro de téléphone invalide.")
                    messages.error(
                        request,
                        "Veuillez fournir un numéro de téléphone valide pour le pays sélectionné.",
                    )
                    return render(
                        request,
                        "authapp/auth_page.html",
                        {"register_form": register_form, "login_form": login_form},
                    )

                # Enregistrer les autres champs
                user.email = register_form.cleaned_data["email"]
                user.password = make_password(register_form.cleaned_data["password"])  # Hachage du mot de passe
                user.save()  # Sauvegarde de l'utilisateur
                messages.success(
                    request,
                    "Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.",
                )
                return redirect("auth_page")  # Redirection pour éviter la double soumission
            else:
                # Messages d'erreur en cas de formulaire invalide
                messages.error(
                    request,
                    "Une erreur s'est produite lors de la création de votre compte. Veuillez vérifier vos informations.",
                )
        elif "login" in request.POST:
            login_form = UserLoginForm(request.POST)
            register_form = UserRegistrationForm()
            if login_form.is_valid():
                phone = login_form.cleaned_data["phone"]
                password = login_form.cleaned_data["password"]
                try:
                    user = User.objects.get(phone=phone)
                    if user.check_password(password):
                        # Logique pour connecter l'utilisateur
                        messages.success(request, "Connexion réussie.")
                    else:
                        messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")
                except User.DoesNotExist:
                    messages.error(request, "Numéro de téléphone ou mot de passe incorrect.")
            else:
                messages.error(request, "Veuillez vérifier vos informations de connexion.")
    else:
        # Afficher les formulaires vierges pour les requêtes GET
        register_form = UserRegistrationForm()
        login_form = UserLoginForm()

    # Renvoyer les formulaires au template
    return render(
        request,
        "authapp/auth_page.html",
        {
            "register_form": register_form,
            "login_form": login_form,
        },
    )


# Vues pour la réinitialisation des mots de passe
User = get_user_model()

def password_reset_request(request):
    """Vue pour demander une réinitialisation de mot de passe"""
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                reset_url = request.build_absolute_uri(
                    reverse("authapp:password_reset_confirm", kwargs={"uidb64": user.pk, "token": token})
                )
                # Envoyer le mail
                subject = "Réinitialisation de votre mot de passe"
                message = render_to_string("authapp/password_reset_email.html", {"reset_url": reset_url, "user": user})
                send_mail(subject, message, "noreply@sahelisbeauty.com", [email])
                return HttpResponse("Un email a été envoyé avec des instructions.")
            except User.DoesNotExist:
                form.add_error("email", "Aucun compte trouvé avec cet email.")
    else:
        form = PasswordResetRequestForm()

    return render(request, "authapp/password_reset_request.html", {"form": form})


def password_reset_confirm(request, uidb64, token):
    try:
        user = User.objects.get(pk=uidb64)
    except User.DoesNotExist:
        return HttpResponse("Lien invalide.")

    if not default_token_generator.check_token(user, token):
        return HttpResponse("Lien invalide ou expiré.")

    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mot de passe modifié avec succès.")
            return redirect("authapp:auth_page")  # Redirige vers la page de connexion
    else:
        form = SetPasswordForm(user)

    return render(request, "authapp/password_reset_confirm.html", {"form": form})
