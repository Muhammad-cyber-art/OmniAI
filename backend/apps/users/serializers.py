"""
OmniLab AI - Users Serializers
Registration, profile read/update, and JWT token customization.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import UserProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extend JWT access token with user role and id claims."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        token["username"] = user.username
        return token


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Handles new user registration.
    Creates user + profile + wallet in a single atomic transaction
    (wallet creation is triggered via post_save signal in billing app).
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "role",
            "password",
            "password_confirm",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {
            "role": {"required": False},
        }

    def validate_role(self, value):
        # Prevent self-assignment of privileged roles
        allowed = [User.role.field.choices[0][0], "STUDENT"]  # only STUDENT via registration
        if value not in ("STUDENT", "RECRUITER"):
            raise serializers.ValidationError(
                "Only STUDENT or RECRUITER roles can be self-assigned."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        validate_password(attrs["password"])
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.get_or_create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "bio",
            "avatar_url",
            "linkedin_url",
            "github_url",
            "total_simulations_completed",
            "total_coins_earned",
            "current_streak_days",
            "longest_streak_days",
            "last_activity_date",
            "institution",
            "specialization",
        ]
        read_only_fields = [
            "total_simulations_completed",
            "total_coins_earned",
            "current_streak_days",
            "longest_streak_days",
            "last_activity_date",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    """Full user detail including nested profile. Read-only for sensitive fields."""

    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "is_portfolio_public",
            "is_email_verified",
            "date_joined",
            "profile",
        ]
        read_only_fields = ["id", "email", "role", "is_email_verified", "date_joined"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """Allows updating safe fields. Profile sub-serializer is handled separately."""

    profile = UserProfileSerializer(required=False)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "is_portfolio_public",
            "profile",
        ]

    @transaction.atomic
    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "New passwords do not match."})
        validate_password(attrs["new_password"])
        return attrs

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class PublicStudentPortfolioSerializer(serializers.ModelSerializer):
    """Read-only serializer for RECRUITER access to public portfolios."""

    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "full_name",
            "role",
            "date_joined",
            "profile",
        ]
