import jwt
import datetime
from django.http import JsonResponse
from django.views import View
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import AccUsers
from .protection import token_required
from django.shortcuts import render, redirect


# Secret key for JWT
JWT_SECRET = settings.JWT_SECRET
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_DAYS = 365

# HEALTH CHECK VIEW
class HealthCheckView(View):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"status": "ok", "message": "School API is healthy"}, status=200)
    
# LOGIN PAGE RENDERING VIEW
def login_page(request):
    return render(request, 'school/login.html')

# MARK VIEW PAGE RENDERING VIEW
def mark_view_page(request):
    return render(request, 'school/mark_view.html')


# LOGIN VIEW
@api_view(['POST'])
def login_view(request):
    user_id = request.data.get('id', '').strip()
    password = request.data.get('pass', '').strip()

    try:
        user = AccUsers.objects.get(id__iexact=user_id.strip())
        if user.pass_field.strip() == password:
            payload = {
                'user_id': user.id,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=JWT_EXP_DELTA_DAYS),
                'iat': datetime.datetime.utcnow(),
            }
            token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

            return Response({
                'token': token,
                'user_id': user.id.strip()
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
    except AccUsers.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


