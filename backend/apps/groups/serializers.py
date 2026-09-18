"""
OmniLab AI - Groups Serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.curriculum.models import Course
from apps.curriculum.serializers import CourseListSerializer
from .models import Group, GroupMembership, GroupInvitation

User = get_user_model()


class StudentBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ["id", "email", "username", "full_name"]


class MentorBriefSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = ["id", "email", "username", "full_name"]


class GroupMembershipSerializer(serializers.ModelSerializer):
    student = StudentBriefSerializer(read_only=True)

    class Meta:
        model = GroupMembership
        fields = ["id", "student", "status", "joined_at"]


class GroupListSerializer(serializers.ModelSerializer):
    mentor = MentorBriefSerializer(read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    courses_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "description",
            "mentor",
            "student_count",
            "courses_count",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_courses_count(self, obj) -> int:
        return obj.courses.count()


class GroupDetailSerializer(serializers.ModelSerializer):
    mentor = MentorBriefSerializer(read_only=True)
    courses = CourseListSerializer(many=True, read_only=True)
    students = serializers.SerializerMethodField()
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = [
            "id",
            "name",
            "description",
            "mentor",
            "courses",
            "students",
            "student_count",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_students(self, obj):
        memberships = obj.memberships.select_related("student").filter(status="ACTIVE")
        return GroupMembershipSerializer(memberships, many=True).data


class GroupWriteSerializer(serializers.ModelSerializer):
    course_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Course.objects.all(),
        source="courses",
        required=False,
    )

    class Meta:
        model = Group
        fields = ["id", "name", "description", "course_ids", "is_active"]

    def create(self, validated_data):
        courses = validated_data.pop("courses", [])
        group = Group.objects.create(**validated_data)
        if courses:
            group.courses.set(courses)
        return group

    def update(self, instance, validated_data):
        courses = validated_data.pop("courses", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if courses is not None:
            instance.courses.set(courses)
        return instance


class GroupInvitationSerializer(serializers.ModelSerializer):
    invite_url = serializers.SerializerMethodField()
    is_expired = serializers.BooleanField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = GroupInvitation
        fields = [
            "id",
            "group",
            "token",
            "invite_url",
            "expires_at",
            "max_uses",
            "times_used",
            "is_active",
            "is_expired",
            "is_valid",
            "created_at",
        ]

    def get_invite_url(self, obj) -> str:
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(f"/api/v1/groups/join/{obj.token}/")
        return f"/api/v1/groups/join/{obj.token}/"


class GenerateInviteSerializer(serializers.Serializer):
    expires_in_days = serializers.IntegerField(default=7, min_value=1, max_value=365)
    max_uses = serializers.IntegerField(default=0, min_value=0, help_text="0 = cheksiz foydalanish")


class InvitePreviewSerializer(serializers.Serializer):
    token = serializers.CharField()
    group_id = serializers.UUIDField()
    group_name = serializers.CharField()
    mentor_name = serializers.CharField()
    courses = serializers.ListField()
    is_valid = serializers.BooleanField()
