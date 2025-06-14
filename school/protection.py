# school/protection.py
import jwt
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from functools import wraps
from .models import AccUsers


# Constants
JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = 'HS256'

# Decorator to protect routes
def token_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Step 1: Get the Authorization header
        auth_header = request.headers.get('Authorization')

        # Step 2: Check if token exists and follows "Bearer <token>" format
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'error': 'Authorization header missing or invalid'}, status=status.HTTP_401_UNAUTHORIZED)

        # Step 3: Extract the token from the header
        token = auth_header.split(' ')[1]

        try:
            # Step 4: Decode the token
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get('user_id', '').strip()

            # Step 5: Look up the user in the database
            user = AccUsers.objects.get(id__iexact=user_id)

            # Step 6: Attach the user object to the request for later use
            request.user = user

        except jwt.ExpiredSignatureError:
            return Response({'error': 'Token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        except AccUsers.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Step 7: Proceed to the original view
        return view_func(request, *args, **kwargs)

    return _wrapped_view
