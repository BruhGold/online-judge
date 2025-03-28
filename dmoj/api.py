from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from judge.models import Submission 
from rest_framework_simplejwt.tokens import RefreshToken  
from rest_framework.test import APIClient
from django.test import TestCase

class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)  # Generate refresh token
            return Response({
                'message': 'Login successful',
                'user_id': user.id,
                #'access_token': str(refresh.access_token),  # Include access token in response
                #'refresh_token': str(refresh)  # Include refresh token in response
            }, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


