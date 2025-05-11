from django.contrib.auth import authenticate
from accounts.models import Utilisateur, Client

def check_client_access():
    print("Starting client authentication test...")
    
    # Try to authenticate a client user
    email = 'test@test.com'
    password = 'password123'
    
    user = authenticate(email=email, password=password)
    print(f'Authentication for {email}: {user is not None}')
    
    if user:
        print(f'User id: {user.id}')
        print(f'User account type: {user.account_type}')
        print(f'Case-insensitive check: Is client? {user.account_type.lower() == "client"}')
        
        # Check if client profile exists
        client_exists = Client.objects.filter(user=user).exists()
        print(f'Client profile exists for user: {client_exists}')
        
        # Check by email
        client_by_email = Client.objects.filter(user__email=email).exists()
        print(f'Client profile exists by email: {client_by_email}')
        
        # Check all clients
        all_clients = Client.objects.all()
        print(f'Total client profiles: {all_clients.count()}')
        print("Client profiles:")
        for client in all_clients:
            print(f'- {client.user.email} (User ID: {client.user.id})')
    else:
        print(f'Authentication failed for {email}')
        
        # Check if user exists
        user_exists = Utilisateur.objects.filter(email=email).exists()
        print(f'User with email {email} exists: {user_exists}')
        
        if user_exists:
            db_user = Utilisateur.objects.get(email=email)
            print(f'User from DB: id={db_user.id}, account_type={db_user.account_type}, is_active={db_user.is_active}')

if __name__ == '__main__':
    check_client_access()
