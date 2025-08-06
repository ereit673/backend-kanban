from django.contrib.auth import authenticate, get_user_model

from rest_framework import serializers


User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    """Serializer to represent minimal user information."""

    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        """Return the full name of the user.

        Args:
            obj: User instance.

        Returns:
            str: Concatenated first and last name.
        """
        return f"{obj.first_name} {obj.last_name}".strip()


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer to handle user registration with validation."""

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
        """Ensure the email is unique in the system.

        Args:
            value (str): Email address to validate.

        Raises:
            serializers.ValidationError: If email already exists.

        Returns:
            str: Validated email.
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def validate_fullname(self, value):
        """Validate the fullname field for presence of first and last name.

        Args:
            value (str): Full name string.

        Raises:
            serializers.ValidationError: If fullname is blank or incomplete.

        Returns:
            str: Validated fullname.
        """
        if not value.strip():
            raise serializers.ValidationError("Full name is required.")
        parts = value.strip().split()
        if len(parts) < 2:
            raise serializers.ValidationError(
                "Please enter your full name (first and last name).")
        return value

    def validate(self, data):
        """Validate that password and repeated_password match.

        Args:
            data (dict): Input data.

        Raises:
            serializers.ValidationError: If passwords do not match.

        Returns:
            dict: Validated data.
        """
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({
                'repeated_password': "Passwords don't match"
            })
        return data

    def create(self, validated_data):
        """Create and return a new user instance.

        Args:
            validated_data (dict): Validated data from serializer.

        Returns:
            User: Created user instance.
        """
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
        """Split full name into first and last name, capitalizing both.

        Args:
            fullname (str): Full name string.

        Returns:
            tuple: (first_name, last_name)
        """
        parts = fullname.split(None, 1)
        first = parts[0].capitalize()
        last = parts[1].capitalize() if len(parts) > 1 else ''
        return first, last


class EmailLoginSerializer(serializers.Serializer):
    """Serializer to handle user login validation."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Authenticate user with given email and password.

        Args:
            data (dict): Input login data.

        Raises:
            serializers.ValidationError: If credentials are invalid or missing.

        Returns:
            dict: Validated data including user instance.
        """
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
