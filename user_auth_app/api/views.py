from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import RegistrationSerializer, EmailLoginSerializer, UserMiniSerializer
import random
import string


User = get_user_model()


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        data = {}

        if serializer.is_valid():
            saved_account = serializer.save()
            (token, created) = Token.objects.get_or_create(user=saved_account)
            data = {
                'token': token.key,
                'fullname': f"{saved_account.first_name} {saved_account.last_name}".strip(),
                'email': saved_account.email,
                'user_id': saved_account.id
            }
        else:
            data = serializer.errors

        return Response(data)


class CustomLoginView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        data = {}

        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            data = {
                'token': token.key,
                'fullname': user.get_full_name(),
                'email': user.email,
                'user_id': user.id
            }
        else:
            data = serializer.errors

        return Response(data)


class GuestLoginView(APIView):
    def post(self, request):
        while True:
            username = 'guest_' + \
                ''.join(random.choices(
                    string.ascii_lowercase + string.digits, k=8))
            if not User.objects.filter(username=username).exists():
                break

        user = User.objects.create_user(username=username)
        user.set_unusable_password()
        user.save()

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "username": user.username,
        })


class EmailCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        email = request.query_params.get('email')

        if not email:
            return Response({'detail': 'Email parameter is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Email nicht gefunden. Die Email existiert nicht.'},
                status=status.HTTP_404_NOT_FOUND
            )

        user_data = UserMiniSerializer(user).data
        return Response(user_data)
