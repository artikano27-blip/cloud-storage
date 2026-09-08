from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import login, logout
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from users.authentication import EnforcedSessionAuthentication
from users.exceptions import IsAuthenticatedCustom
from users.serializers import LoginSerializer, RegisterSerializer
from users.services import create_user, authenticate_user

class AuthRateThrottle(AnonRateThrottle):
    rate = "5/minute"  # Не более 5 попыток в минуту для одного IP

class LoginAPIView(generics.GenericAPIView):
    throttle_classes = [AuthRateThrottle]
    serializer_class = LoginSerializer
    authentication_classes = [EnforcedSessionAuthentication]
    permission_classes = []  # Разрешает доступ неавторизованным пользователям

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate_user(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        login(request, user)

        return Response({"username": user.username}, status=status.HTTP_200_OK)


class RegisterAPIView(generics.GenericAPIView):
    throttle_classes = [AuthRateThrottle]
    serializer_class = RegisterSerializer
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = create_user(
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        login(request, user)

        return Response({"username": user.username}, status=status.HTTP_201_CREATED)


class UserAPIView(APIView):
    permission_classes = [IsAuthenticatedCustom]

    def get(self, request, *args, **kwargs):
        return Response({"username": request.user.username})


class SignOutView(APIView):
    permission_classes = [IsAuthenticatedCustom]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)
