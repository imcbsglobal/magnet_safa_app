# school/protection.py
from functools import wraps
from inspect import signature
import jwt
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from .models import AccUsers

JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = 'HS256'

def token_required(view_func):
    @wraps(view_func)
    def _wrapped_view(*args, **kwargs):
        # Detect if it's a method (class-based view)
        if len(args) >= 2 and hasattr(args[0], '__class__'):
            self_or_cls = args[0]
            request = args[1]
            remaining_args = args[2:]
        else:
            # Function-based view
            request = args[0]
            self_or_cls = None
            remaining_args = args[1:]

        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'error': 'Authorization header missing or invalid'}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_id = payload.get('user_id', '').strip()
            user = AccUsers.objects.get(id__iexact=user_id)
            request.user = user
        except jwt.ExpiredSignatureError:
            return Response({'error': 'Token has expired'}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)
        except AccUsers.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Re-call the view with proper arguments
        if self_or_cls:
            return view_func(self_or_cls, request, *remaining_args, **kwargs)
        else:
            return view_func(request, *remaining_args, **kwargs)

    return _wrapped_view
