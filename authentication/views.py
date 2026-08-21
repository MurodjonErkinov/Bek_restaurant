from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .permissions import IsEmployee
from .serializers import (
    CurrentUserSerializer,
    EmployeeTokenObtainPairSerializer,
    EmployeeTokenRefreshSerializer,
    LogoutSerializer,
)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = EmployeeTokenObtainPairSerializer


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    serializer_class = EmployeeTokenRefreshSerializer


class LogoutView(APIView):
    permission_classes = [IsEmployee]

    def post(self, request):
        serializer = LogoutSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsEmployee]

    def get(self, request):
        return Response(CurrentUserSerializer(request.user).data)