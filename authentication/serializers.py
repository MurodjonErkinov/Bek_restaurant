from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from core.phone import normalize_uzbek_phone

from .permissions import EMPLOYEE_ROLES


User = get_user_model()


class CurrentUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'role',
            'is_active',
            'is_staff',
        ]
        read_only_fields = fields

    def get_full_name(self, user):
        return user.get_full_name() or user.phone


class EmployeeTokenObtainPairSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate_phone(self, value):
        try:
            return normalize_uzbek_phone(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc

    def validate(self, attrs):
        try:
            account = User.objects.get(phone=attrs['phone'])
        except (User.DoesNotExist, User.MultipleObjectsReturned) as exc:
            raise AuthenticationFailed('Telefon raqam yoki parol noto‘g‘ri.') from exc
        user = authenticate(
            request=self.context.get('request'),
            username=account.username,
            password=attrs['password'],
        )
        if user is None:
            raise AuthenticationFailed('Telefon raqam yoki parol noto‘g‘ri.')
        if user.role not in EMPLOYEE_ROLES and not user.is_superuser:
            raise AuthenticationFailed('Bu xodim roli uchun API kirish yopiq.')
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': CurrentUserSerializer(user).data,
        }


class EmployeeTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = RefreshToken(attrs['refresh'])
        user_id = refresh.payload.get(api_settings.USER_ID_CLAIM)
        try:
            user = User.objects.get(
                **{api_settings.USER_ID_FIELD: user_id},
            )
        except User.DoesNotExist as exc:
            raise AuthenticationFailed('User topilmadi.') from exc
        if not user.is_active:
            raise AuthenticationFailed('User faol emas.')
        if user.role not in EMPLOYEE_ROLES and not user.is_superuser:
            raise AuthenticationFailed('Bu xodim roli uchun API kirish yopiq.')
        return super().validate(attrs)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            token = RefreshToken(value)
        except TokenError as exc:
            raise serializers.ValidationError('Refresh token noto‘g‘ri yoki eskirgan.') from exc
        request = self.context['request']
        user_id = token.payload.get(api_settings.USER_ID_CLAIM)
        if str(user_id) != str(request.user.pk):
            raise serializers.ValidationError('Refresh token boshqa userga tegishli.')
        token.blacklist()
        return value
