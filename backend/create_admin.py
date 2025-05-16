"""
Script to create an admin user for ServicesBLADI.
Run this from the command line with:
python create_admin.py [email] [password] [name] [first_name]

If no arguments are provided, the script will prompt for input.
"""
import os
import sys
import django
import getpass

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'servicesbladi.settings')
django.setup()

# Import the user model
from accounts.models import Utilisateur

def create_admin(email=None, password=None, name=None, first_name=None, interactive=True):
    """Create an admin user for the application"""
    # Get email
    if not email and interactive:
        email = input('Admin email: ')
    elif not email:
        print("Error: Email is required")
        return False
    
    # Check if the user already exists
    user_exists = Utilisateur.objects.filter(email=email).exists()
    if user_exists and interactive:
        update = input(f'User with email {email} already exists. Update as admin? (y/n): ')
        if update.lower() != 'y':
            return False
    
    # Get name
    if not name and interactive:
        name = input('Name: ')
    elif not name:
        name = "Admin"
        
    # Get first name
    if not first_name and interactive:
        first_name = input('First name: ')
    elif not first_name:
        first_name = "Admin"
        
    # Get password
    if not password and interactive:
        password = getpass.getpass('Password: ')
        password_confirm = getpass.getpass('Confirm password: ')
        if password != password_confirm:
            print("Passwords don't match!")
            return False
    elif not password:
        print("Error: Password is required")
        return False
    
    # Create or update the admin user
    try:
        # If user exists, update it
        if user_exists:
            user = Utilisateur.objects.get(email=email)
            user.name = name
            user.first_name = first_name
            user.set_password(password)
            user.account_type = 'admin'
            user.is_staff = True
            user.is_superuser = True
            user.is_verified = True
            user.save()
            print(f"Updated user {email} as admin successfully!")
        else:
            # Create new admin user
            admin = Utilisateur.objects.create_user(
                email=email,
                password=password,
                name=name,
                first_name=first_name,
                account_type='admin',
                is_staff=True,
                is_superuser=True,
                is_verified=True
            )
            print(f"Created new admin user {email} successfully!")
        
        print("\nAdmin Login Information:")
        print(f"URL: http://127.0.0.1:8000/accounts/management/secure8765/login/")
        print(f"Email: {email}")
        print(f"Security Code: 87654321")
        
        return True
        
    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        return False

if __name__ == '__main__':
    # Check if we have command line arguments
    if len(sys.argv) >= 5:
        # Use command line arguments
        email = sys.argv[1]
        password = sys.argv[2]
        name = sys.argv[3]
        first_name = sys.argv[4]
        create_admin(email, password, name, first_name, interactive=False)
    elif len(sys.argv) >= 2:
        # Email provided, prompt for rest
        email = sys.argv[1]
        create_admin(email=email)
    else:
        # Interactive mode
        create_admin()