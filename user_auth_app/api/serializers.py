from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate


User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class RegistrationSerializer(serializers.ModelSerializer):
    repeated_password = serializers.CharField(write_only=True)
    fullname = serializers.CharField(
        write_only=True, required=True, allow_blank=False
    )

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def validate_fullname(self, value):
        if not value.strip():
            raise serializers.ValidationError("Full name is required.")
        parts = value.strip().split()
        if len(parts) < 2:
            raise serializers.ValidationError(
                "Please enter your full name (first and last name).")
        return value

    def validate(self, data):
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({
                'repeated_password': "Passwords don't match"
            })
        return data

    def create(self, validated_data):
        validated_data.pop('repeated_password', None)
        fullname = validated_data.pop('fullname', '').strip()
        first_name, last_name = self.split_fullname(fullname)

        user = User(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

    def split_fullname(self, fullname):
        parts = fullname.split(None, 1)
        first = parts[0].capitalize()
        last = parts[1].capitalize() if len(parts) > 1 else ''
        return first, last


class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
        else:
            raise serializers.ValidationError(
                'Must provide email and password')

        data['user'] = user
        return data
