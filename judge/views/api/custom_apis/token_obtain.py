from rest_framework_simplejwt.views import TokenObtainPairView as OldTokenObtainPairView
from ..serializers.token_obtain import CustomTokenObtainPairSerializer

class TokenObtainPairView(OldTokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer