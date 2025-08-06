from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import RegistrationSerializer, EmailLoginSerializer, UserMiniSerializer


User = get_user_model()


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            saved_account = serializer.save()
            token, created = Token.objects.get_or_create(user=saved_account)

            return Response({
                'token': token.key,
                'fullname': f"{saved_account.first_name} {saved_account.last_name}".strip(),
                'email': saved_account.email,
                'user_id': saved_account.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def build_success_response(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        return {
            'token': token.key,
            'fullname': f"{user.first_name} {user.last_name}".strip(),
            'email': user.email,
            'user_id': user.id
        }


class CustomLoginView(ObtainAuthToken):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            return Response(self.build_success_response(user), status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def build_success_response(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        return {
            'token': token.key,
            'fullname': user.get_full_name(),
            'email': user.email,
            'user_id': user.id
        }


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
