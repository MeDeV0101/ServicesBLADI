from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
import logging

from .models import Utilisateur, Client, Expert, Address, Notification
from .forms import UserEditForm, CustomPasswordChangeForm  # Added form imports
from custom_requests.models import Document, Message

# Set up logger
logger = logging.getLogger(__name__)

# Authentication views
def resend_verification_email(request, user):
    """Resend verification email to user"""
    try:
        # Log resend attempt
        logger.info(f"Attempting to resend verification email to {user.email}")
        
        # Send activation email
        email_sent = send_activation_email(user, request)
        
        if email_sent:
            messages.success(request, _('Un nouvel email de vérification a été envoyé à votre adresse email.'))
            logger.info(f"Successfully resent verification email to {user.email}")
        else:
            messages.error(request, _('Erreur lors de l\'envoi de l\'email de vérification. Veuillez réessayer.'))
            logger.error(f"Failed to resend verification email to {user.email}")
            
        return email_sent
        
    except Exception as e:
        logger.error(f"Error in resend_verification_email: {str(e)}")
        messages.error(request, _('Une erreur est survenue. Veuillez réessayer.'))
        return False

def custom_login_view(request):
    """Custom login view that handles both form and API requests"""
    # Clear any existing service-related error messages
    storage = messages.get_messages(request)
    # Convert messages to a list to extract them
    existing_messages = list(storage)
    # Clear storage
    storage.used = True

    # Restore only authentication-related messages, discard service-related ones
    for msg in existing_messages:
        if 'No active services found' not in str(msg):
            messages.add_message(request, msg.level, msg.message)
    
    if request.method == 'POST':
        # Check if this is an API call
        if request.content_type == 'application/json':
            try:
                import json
                data = json.loads(request.body)
                email = data.get('email', '')
                password = data.get('password', '')
                
                user = authenticate(request, email=email, password=password)
                
                if user is not None:
                    if not user.is_active:
                        # Resend verification email
                        resend_verification_email(request, user)
                        return JsonResponse({
                            'success': False,
                            'message': _('Votre compte n\'est pas encore vérifié. Un nouvel email de vérification a été envoyé à votre adresse email.'),
                            'needs_verification': True
                        }, status=400)
                    
                    print(f"API login successful for user: {user.email}, account_type: {user.account_type}")
                    login(request, user)
                    redirect_url = request.GET.get('next', '/accounts/dashboard/')
                    print(f"API login redirecting to: {redirect_url}")
                    return JsonResponse({
                        'success': True,
                        'redirect': redirect_url,
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'name': user.name,
                            'first_name': user.first_name,
                            'account_type': user.account_type,
                        }
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': _('Email ou mot de passe incorrect')
                    }, status=400)
                    
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=400)
        
        # Handle form submission
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, _('Veuillez fournir votre email et mot de passe'))
            return render(request, 'login.html')
        
        # Try authentication
        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if not user.is_active:
                # Resend verification email
                resend_verification_email(request, user)
                messages.warning(request, _('Votre compte n\'est pas encore vérifié. Un nouvel email de vérification a été envoyé à votre adresse email.'))
                return render(request, 'login.html')
                
            login(request, user)
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, _('Email ou mot de passe incorrect'))
    
    return render(request, 'login.html')

# Admin authentication views
def admin_login_view(request):
    """Custom login view specifically for admin users - with enhanced security"""
    
    # Track login attempts for security (to detect brute force attacks)
    client_ip = request.META.get('REMOTE_ADDR', '')
    current_time = timezone.now()
    
    # Simple rate limiting - you would implement this properly in production
    # with a proper rate limiting solution
    
    # Clear any existing messages
    storage = messages.get_messages(request)
    storage.used = True
    
    # If user is already authenticated as admin, redirect to admin dashboard
    if request.user.is_authenticated and request.user.account_type.lower() == 'admin':
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        security_code = request.POST.get('security_code')
        
        # Add additional security layer - a fixed security code
        # In production, use a proper 2FA solution instead
        if security_code != '87654321':
            messages.error(request, _("Code de sécurité invalide."))
            print(f"Failed admin login attempt with invalid security code from IP: {client_ip}")
            return redirect('accounts:admin_login_view')
            
        user = authenticate(request, email=email, password=password)
        
        if user is not None and user.account_type.lower() == 'admin':
            print(f"Admin login successful for: {user.email} from IP: {client_ip}")
            login(request, user)
            
            # Log successful admin login for security audit
            return redirect('admin_dashboard')
        else:
            # Either the credentials are wrong or the user is not an admin
            if user is not None and user.account_type.lower() != 'admin':
                messages.error(request, _("Vous n'avez pas les autorisations nécessaires pour accéder au panel administrateur."))
            else:
                messages.error(request, _("Email ou mot de passe incorrect."))
            
            # Log failed login attempt
            print(f"Failed admin login attempt for email: {email} from IP: {client_ip}")
            return redirect('accounts:admin_login_view')
    
    return render(request, 'admin/login.html')

def create_admin_user(request):
    """View to create a new admin user (protected, only accessible to existing admins)"""
    if not request.user.is_authenticated or request.user.account_type.lower() != 'admin':
        raise PermissionDenied
    
    if request.method == 'POST':
        email = request.POST.get('email')
        name = request.POST.get('name')
        first_name = request.POST.get('first_name')
        password = request.POST.get('password')
        
        if email and password:
            try:
                # Check if user already exists
                if Utilisateur.objects.filter(email=email).exists():
                    messages.error(request, _("Un utilisateur avec cet email existe déjà."))
                    return redirect('admin_users')
                
                # Create the admin user
                user = Utilisateur.objects.create_user(
                    email=email,
                    name=name,
                    first_name=first_name,
                    password=password,
                    account_type='admin',
                    is_verified=True
                )
                
                messages.success(request, _("Administrateur créé avec succès."))
                return redirect('admin_users')
            except Exception as e:
                messages.error(request, str(e))
                return redirect('admin_users')
    
    # GET request - show the form
    return render(request, 'admin/create_admin.html')

def send_activation_email(user, request):
    """Send activation email to user"""
    try:
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Build activation link
        activation_link = request.build_absolute_uri(
            reverse('accounts:activate', kwargs={'uidb64': uid, 'token': token})
        )
        
        # Render email template
        context = {
            'user': user,
            'activation_link': activation_link,
            'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
        }
        html_message = render_to_string('accounts/emails/activation_email.html', context)
        
        # Log email attempt
        logger.info(f"Attempting to send activation email to {user.email}")
        
        # Check email configuration
        if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
            logger.error("Email configuration is incomplete. Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD settings.")
            return False
        
        # Send email
        send_mail(
            subject=_('Activez votre compte ServiceBladi'),
            message=f'Pour activer votre compte, cliquez sur ce lien : {activation_link}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False  # Raise exceptions for debugging
        )
        
        logger.info(f"Successfully sent activation email to {user.email}")
        return True
        
    except BadHeaderError as e:
        logger.error(f"Invalid header found while sending email to {user.email}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Failed to send activation email to {user.email}: {str(e)}")
        # Log the full traceback for debugging
        import traceback
        logger.error(traceback.format_exc())
        return False

def activate_account(request, uidb64, token):
    """Activate user account"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Utilisateur.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, _('Votre compte a été activé avec succès.'))
        return render(request, 'accounts/activation_success.html')
    else:
        return render(request, 'accounts/activation_error.html')

def register_view(request):
    """Handle client registration"""
    if request.method == 'POST':
        # Set account type to client
        request.POST = request.POST.copy()
        request.POST['user_type'] = 'client'
        
        # Extract user data from form
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        name = request.POST.get('last_name', '')
        first_name = request.POST.get('first_name', '')
        phone = request.POST.get('phone', '')
        
        # Validate data
        if not all([email, password, name, first_name, phone]):
            messages.error(request, _('Veuillez remplir tous les champs obligatoires'))
            return render(request, 'register.html')
        
        # Check if passwords match
        if password != password_confirm:
            messages.error(request, _('Les mots de passe ne correspondent pas'))
            return render(request, 'register.html')
        
        # Check if user already exists
        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, _('Cette adresse email est déjà enregistrée'))
            return render(request, 'register.html')
        
        try:
            # Create user with is_active=False
            user = Utilisateur.objects.create_user(
                email=email,
                password=password,
                name=name,
                first_name=first_name,
                phone=phone,
                account_type='client',
                preferred_languages=request.POST.get('preferred_language', 'fr'),
                is_active=False  # Set to False until email verification
            )
            
            # Create client profile
            Client.objects.create(
                user=user,
                mre_status=True,
                origin_country='Maroc',
                last_visit=request.POST.get('last_visit', None)
            )
            
            # Create address if provided
            country = request.POST.get('residence_country', '')
            if country:
                Address.objects.create(
                    user=user,
                    country=country,
                    address_type='HOME',
                )
            
            # Send activation email
            email_sent = send_activation_email(user, request)
            if not email_sent:
                # If email fails, delete the user and show error
                user.delete()
                messages.error(request, _('Erreur lors de l\'envoi de l\'email de vérification. Veuillez réessayer.'))
                return render(request, 'register.html')
            
            messages.success(request, _('Votre compte a été créé. Veuillez vérifier votre email pour activer votre compte.'))
            return redirect('accounts:login')
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            messages.error(request, str(e))
            return render(request, 'register.html')
    
    # GET request - show registration form
    context = {
        'countries': settings.COUNTRIES,
    }
    return render(request, 'register.html', context)

def register_expert_view(request):
    """Handle expert registration"""
    if request.method == 'POST':
        # Set account type to expert
        request.POST = request.POST.copy()
        request.POST['user_type'] = 'expert'
        
        # Extract user data from form
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        name = request.POST.get('last_name', '')
        first_name = request.POST.get('first_name', '')
        phone = request.POST.get('phone', '')
        expertise = request.POST.get('expertise', '')
        experience = request.POST.get('experience', 0)
        
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Validate data
        if not all([email, password, name, first_name, phone, expertise]):
            error_msg = _('Veuillez remplir tous les champs obligatoires')
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'register_expert.html', {'countries': settings.COUNTRIES})
        
        # Check if passwords match
        if password != password_confirm:
            error_msg = _('Les mots de passe ne correspondent pas')
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'register_expert.html', {'countries': settings.COUNTRIES})
        
        # Check if user already exists
        if Utilisateur.objects.filter(email=email).exists():
            error_msg = _('Cette adresse email est déjà enregistrée')
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'register_expert.html', {'countries': settings.COUNTRIES})
        
        try:
            # Create user with is_active=False
            user = Utilisateur.objects.create_user(
                email=email,
                password=password,
                name=name,
                first_name=first_name,
                phone=phone,
                account_type='expert',
                preferred_languages='fr',
                is_active=False  # Set to False until email verification
            )
            
            # Create expert profile
            Expert.objects.create(
                user=user,
                specialty=expertise,
                biography='',
                spoken_languages='fr',
                hourly_rate=0,
                years_of_experience=experience or 0
            )
            
            # Send activation email
            send_activation_email(user, request)
            
            # For AJAX requests, return success response
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': _('Expert enregistré avec succès. Veuillez vérifier votre email pour activer votre compte.')
                })
            
            messages.success(request, _('Votre compte a été créé. Veuillez vérifier votre email pour activer votre compte.'))
            return redirect('accounts:login')
            
        except Exception as e:
            error_msg = str(e)
            if is_ajax:
                return JsonResponse({'success': False, 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'register_expert.html', {'countries': settings.COUNTRIES})
    
    # GET request - show registration form
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)
        
    context = {
        'countries': settings.COUNTRIES,
    }
    return render(request, 'register_expert.html', context)

# Dashboard views
@login_required
def dashboard_redirect_view(request):
    """Redirect users to the appropriate dashboard based on their account type"""
    print(f"Dashboard redirect for user: {request.user.email}, account_type={request.user.account_type}")
    
    # Check account type case-insensitively
    account_type = request.user.account_type.lower()
    
    if account_type == 'admin':
        print("Redirecting to admin dashboard")
        return redirect('admin_dashboard')
    elif account_type == 'expert':
        print("Redirecting to expert dashboard")
        return redirect('expert_dashboard')
    elif account_type == 'client':
        print("Redirecting to client dashboard")
        return redirect('client_dashboard')
    else:
        print(f"Unknown account type: {account_type}, redirecting to home")
        return redirect('home')

# Profile views
@login_required
def profile_view(request):
    """View user's own profile"""
    # Get the user's profile information
    user = request.user
    
    # Get user's address
    try:
        address = Address.objects.get(user=user, address_type='HOME')
    except Address.DoesNotExist:
        address = None
    
    # Get additional profile info based on user type
    if user.account_type == 'CLIENT':
        try:
            profile = Client.objects.get(user=user)
        except Client.DoesNotExist:
            profile = None
    elif user.account_type == 'EXPERT':
        try:
            profile = Expert.objects.get(user=user)
        except Expert.DoesNotExist:
            profile = None
    else:
        profile = None
    
    context = {
        'user': user,
        'address': address,
        'profile': profile,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile_view(request):
    user = request.user
    user_form = UserEditForm(instance=user)
    password_form = CustomPasswordChangeForm(user)

    if request.method == 'POST':
        if 'update_profile' in request.POST:  # Identifier for profile form
            user_form = UserEditForm(request.POST, instance=user)
            if user_form.is_valid():
                user_form.save()
                # Update or create address
                address_data = {
                    'street': request.POST.get('street', ''),
                    'city': request.POST.get('city', ''),
                    'postal_code': request.POST.get('postal_code', ''),
                    'country': request.POST.get('country', ''),
                }
                Address.objects.update_or_create(
                    user=user,
                    address_type='HOME',
                    defaults=address_data
                )
                # Update additional profile info based on user type
                if user.account_type == 'CLIENT':
                    Client.objects.update_or_create(
                        user=user,
                        defaults={
                            'preferred_language': request.POST.get('preferred_language', 'fr'),
                        }
                    )
                elif user.account_type == 'EXPERT':
                    Expert.objects.update_or_create(
                        user=user,
                        defaults={
                            'title': request.POST.get('title', ''),
                            'specialty': request.POST.get('specialty', ''),
                            'bio': request.POST.get('bio', ''),
                            'experience_years': request.POST.get('experience_years', 0),
                            'languages': request.POST.get('languages', 'fr'),
                        }
                    )
                messages.success(request, _('Votre profil a été mis à jour avec succès.'))
                return redirect('accounts:edit_profile') # Redirect back to the edit page
            else:
                messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))

        elif 'change_password' in request.POST:  # Identifier for password change form
            password_form = CustomPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, _('Votre mot de passe a été changé avec succès.'))
                return redirect('accounts:edit_profile') # Redirect back to the edit page
            else:
                messages.error(request, _('Veuillez corriger les erreurs de mot de passe ci-dessous.'))

    # GET request handling (or if forms are invalid on POST)
    try:
        address = Address.objects.get(user=user, address_type='HOME')
    except Address.DoesNotExist:
        address = None

    profile_specific = None
    if user.account_type == 'CLIENT':
        try:
            profile_specific = Client.objects.get(user=user)
        except Client.DoesNotExist:
            pass
    elif user.account_type == 'EXPERT':
        try:
            profile_specific = Expert.objects.get(user=user)
        except Expert.DoesNotExist:
            pass

    context = {
        'user_form': user_form,
        'password_form': password_form,
        'user': user,
        'address': address,
        'profile_specific': profile_specific, # Changed from 'profile' to 'profile_specific'
        'countries': settings.COUNTRIES,
        'account_type': user.account_type # Pass account_type for template logic
    }
    return render(request, 'accounts/edit_profile.html', context)

# Client specific views
@login_required
def client_profile_view(request):
    """View for client profile"""
    # Check if user is a client
    if request.user.account_type != 'CLIENT':
        raise PermissionDenied
    
    return profile_view(request)

@login_required
def client_documents_view(request):
    """View client's documents"""
    # Check if user is a client
    if request.user.account_type != 'CLIENT':
        raise PermissionDenied
    
    # Get client's documents
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    
    context = {
        'documents': documents,
    }
    
    return render(request, 'accounts/client_documents.html', context)

# Expert specific views
@login_required
def expert_profile_view(request):
    """View for expert profile"""
    # Check if user is an expert
    if request.user.account_type != 'EXPERT':
        raise PermissionDenied
    
    return profile_view(request)

@login_required
def expert_availability_view(request):
    """Manage expert's availability"""
    # Check if user is an expert
    if request.user.account_type != 'EXPERT':
        raise PermissionDenied
    
    expert = get_object_or_404(Expert, user=request.user)
    
    if request.method == 'POST':
        # Update availability status
        status = request.POST.get('availability_status')
        if status in ['AVAILABLE', 'BUSY', 'UNAVAILABLE']:
            expert.availability_status = status
            expert.save()
        
        return redirect('accounts:expert_profile')
    
    context = {
        'expert': expert,
    }
    
    return render(request, 'accounts/expert_availability.html', context)

@login_required
def expert_services_view(request):
    """Manage services offered by expert"""
    # Check if user is an expert
    if request.user.account_type != 'EXPERT':
        raise PermissionDenied
    
    expert = get_object_or_404(Expert, user=request.user)
    
    # Get services offered by expert
    services = expert.services.all()
    
    context = {
        'expert': expert,
        'services': services,
    }
    
    return render(request, 'accounts/expert_services.html', context)

# Admin specific views
@login_required
def admin_users_view(request):
    """Admin view for user management"""
    # Check if user is an admin
    if request.user.account_type != 'ADMIN':
        raise PermissionDenied
    
    # Get all users
    users = Utilisateur.objects.all().order_by('-date_joined')
    
    context = {
        'users': users,
    }
    
    return render(request, 'accounts/admin_users.html', context)

@login_required
def admin_user_detail_view(request, user_id):
    """Admin view for user details"""
    # Check if user is an admin
    if request.user.account_type != 'ADMIN':
        raise PermissionDenied
    
    # Get the user
    user = get_object_or_404(Utilisateur, id=user_id)
    
    # Get user's address
    try:
        address = Address.objects.get(user=user, address_type='HOME')
    except Address.DoesNotExist:
        address = None
    
    # Get additional profile info based on user type
    if user.account_type == 'CLIENT':
        try:
            profile = Client.objects.get(user=user)
        except Client.DoesNotExist:
            profile = None
    elif user.account_type == 'EXPERT':
        try:
            profile = Expert.objects.get(user=user)
        except Expert.DoesNotExist:
            profile = None
    else:
        profile = None
    
    context = {
        'target_user': user,  # Use 'target_user' to avoid conflict with 'user' (the admin)
        'address': address,
        'profile': profile,
    }
    
    return render(request, 'accounts/admin_user_detail.html', context)

@login_required
def admin_create_user_view(request):
    """Admin view to create a new user"""
    # Check if user is an admin
    if request.user.account_type != 'ADMIN':
        raise PermissionDenied
    
    if request.method == 'POST':
        # Extract user data
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        name = request.POST.get('name', '')
        first_name = request.POST.get('first_name', '')
        phone = request.POST.get('phone', '')
        user_type = request.POST.get('user_type', 'CLIENT')
        
        # Create user
        user = Utilisateur.objects.create_user(
            email=email,
            password=password,
            name=name,
            first_name=first_name,
            phone=phone,
            account_type=user_type,
        )
        
        # Create profile based on user type
        if user_type == 'CLIENT':
            Client.objects.create(
                user=user,
                preferred_language=request.POST.get('preferred_language', 'fr'),
            )
        elif user_type == 'EXPERT':
            Expert.objects.create(
                user=user,
                specialty=request.POST.get('specialty', ''),
                biography=request.POST.get('bio', ''),
                spoken_languages=request.POST.get('languages', 'fr') or 'fr',
                hourly_rate=0  # Default value
            )
        
        # Create address if provided
        street = request.POST.get('street', '')
        if street:
            Address.objects.create(
                user=user,
                street=street,
                city=request.POST.get('city', ''),
                postal_code=request.POST.get('postal_code', ''),
                country=request.POST.get('country', ''),
                address_type='HOME',
            )
        
        return redirect('accounts:admin_users')
    
    context = {
        'countries': settings.COUNTRIES,
    }
    
    return render(request, 'accounts/admin_create_user.html', context)

# API endpoints
@csrf_exempt
@login_required
def api_profile(request):
    """API endpoint to get user profile"""
    user = request.user
    
    # Get user's address
    try:
        address = Address.objects.get(user=user, address_type='HOME')
        address_data = {
            'street': address.street,
            'city': address.city,
            'postal_code': address.postal_code,
            'country': address.country,
        }
    except Address.DoesNotExist:
        address_data = {}
    
    # Get additional profile info based on user type
    if user.account_type == 'CLIENT':
        try:
            profile = Client.objects.get(user=user)
            profile_data = {
                'preferred_language': profile.preferred_language,
            }
        except Client.DoesNotExist:
            profile_data = {}
    elif user.account_type == 'EXPERT':
        try:
            profile = Expert.objects.get(user=user)
            profile_data = {
                'title': profile.title,
                'specialty': profile.specialty,
                'bio': profile.bio,
                'experience_years': profile.experience_years,
                'languages': profile.languages,
                'availability_status': profile.availability_status,
            }
        except Expert.DoesNotExist:
            profile_data = {}
    else:
        profile_data = {}
    
    # Prepare response data
    user_data = {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'first_name': user.first_name,
        'phone': user.phone,
        'account_type': user.account_type,
        'date_joined': user.date_joined.isoformat(),
        'is_active': user.is_active,
        'address': address_data,
        'profile': profile_data,
    }
    
    return JsonResponse({
        'success': True,
        'user': user_data
    })

@csrf_exempt
@login_required
def api_update_profile(request):
    """API endpoint to update user profile"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'message': _('Method not allowed')
        }, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        user = request.user
        
        # Update user data
        user.name = data.get('name', user.name)
        user.first_name = data.get('first_name', user.first_name)
        user.phone = data.get('phone', user.phone)
        user.save()
        
        # Update or create address
        address_data = data.get('address', {})
        if address_data:
            Address.objects.update_or_create(
                user=user,
                address_type='HOME',
                defaults={
                    'street': address_data.get('street', ''),
                    'city': address_data.get('city', ''),
                    'postal_code': address_data.get('postal_code', ''),
                    'country': address_data.get('country', ''),
                }
            )
        
        # Update additional profile info based on user type
        profile_data = data.get('profile', {})
        if user.account_type == 'CLIENT':
            Client.objects.update_or_create(
                user=user,
                defaults={
                    'preferred_language': profile_data.get('preferred_language', 'fr'),
                }
            )
        elif user.account_type == 'EXPERT':
            Expert.objects.update_or_create(
                user=user,
                defaults={
                    'title': profile_data.get('title', ''),
                    'specialty': profile_data.get('specialty', ''),
                    'bio': profile_data.get('bio', ''),
                    'experience_years': profile_data.get('experience_years', 0),
                    'languages': profile_data.get('languages', 'fr'),
                    'availability_status': profile_data.get('availability_status', 'AVAILABLE'),
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': _('Profile updated successfully')
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
