from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.contrib import messages

from .models import Utilisateur, Client, Expert, Address, Notification
from requests.models import Document, Message

# Authentication views
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
                        'message': _('Invalid email or password')
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
            messages.error(request, _('Please provide both email and password'))
            return render(request, 'login.html')
        
        # Debug: Check if user exists
        try:
            user_exists = Utilisateur.objects.filter(email=email).exists()
            print(f"User exists: {user_exists}")
        except Exception as e:
            print(f"Error checking user existence: {str(e)}")
        
        # Debug: Try to get user directly
        try:
            user = Utilisateur.objects.get(email=email)
            print(f"Found user: {user.email}, is_active: {user.is_active}")
        except Utilisateur.DoesNotExist:
            print(f"No user found with email: {email}")
        except Exception as e:
            print(f"Error getting user: {str(e)}")
            
        # Try authentication
        user = authenticate(request, email=email, password=password)
        print(f"Authentication result: {user is not None}")
        
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, _('Invalid email or password'))
    
    return render(request, 'login.html')

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        # Extract user data from form
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        name = request.POST.get('last_name', '')  # last_name is the name field in the form
        first_name = request.POST.get('first_name', '')
        phone = request.POST.get('phone', '')
        account_type = request.POST.get('user_type', 'client').lower()  # Convert to lowercase to match model choices
        preferred_language = request.POST.get('preferred_language', 'fr')
        
        # Validate data
        if not all([email, password, name, first_name, phone]):
            messages.error(request, _('Please provide all required fields'))
            return render(request, 'register.html')
        
        # Check if passwords match
        if password != password_confirm:
            messages.error(request, _('Passwords do not match'))
            return render(request, 'register.html')
        
        # Check if user already exists
        if Utilisateur.objects.filter(email=email).exists():
            messages.error(request, _('Email already registered'))
            return render(request, 'register.html')
        
        try:
            # Create user
            user = Utilisateur.objects.create_user(
                email=email,
                password=password,
                name=name,
                first_name=first_name,
                phone=phone,
                account_type=account_type,
                preferred_languages=preferred_language,
            )
            
            # Create profile based on user type
            if account_type == 'client':
                Client.objects.create(
                    user=user,
                    mre_status=True,
                    origin_country='Maroc',
                )
            elif account_type == 'expert':
                Expert.objects.create(
                    user=user,
                    specialty=request.POST.get('expertise', ''),
                    biography=request.POST.get('bio', ''),
                    spoken_languages=request.POST.get('languages', 'fr') or 'fr',
                    hourly_rate=0  # Default value
                )
            
            # Create address if provided
            country = request.POST.get('residence_country', '')
            if country:
                Address.objects.create(
                    user=user,
                    country=country,
                    address_type='HOME',
                )
            
            # Log the user in
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('accounts:dashboard_redirect')
            
        except Exception as e:
            messages.error(request, str(e))
            return render(request, 'register.html')
    
    # GET request - show registration form
    context = {
        'countries': settings.COUNTRIES,
    }
    return render(request, 'register.html', context)

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
    """Edit user's own profile"""
    # Get the user's profile information
    user = request.user
    
    if request.method == 'POST':
        # Update user data
        user.name = request.POST.get('name', user.name)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.phone = request.POST.get('phone', user.phone)
        user.save()
        
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
        
        return redirect('accounts:profile')
    
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
        'countries': settings.COUNTRIES,
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
