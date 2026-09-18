"""
OmniLab AI - Groups Admin Configuration
"""
from django.contrib import admin
from .models import Group, GroupMembership, GroupInvitation


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 0
    raw_id_fields = ("student",)
    readonly_fields = ("joined_at",)


class GroupInvitationInline(admin.TabularInline):
    model = GroupInvitation
    extra = 0
    readonly_fields = ("token", "times_used", "created_at")


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "mentor", "student_count", "is_active", "created_at")
    list_filter = ("is_active", "mentor")
    search_fields = ("name", "mentor__email", "mentor__username")
    filter_horizontal = ("courses",)
    inlines = [GroupMembershipInline, GroupInvitationInline]


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("group", "student", "status", "joined_at")
    list_filter = ("status", "group")
    search_fields = ("group__name", "student__email", "student__username")


@admin.register(GroupInvitation)
class GroupInvitationAdmin(admin.ModelAdmin):
    list_display = ("group", "token", "times_used", "max_uses", "is_active", "expires_at", "created_at")
    list_filter = ("is_active", "group")
    search_fields = ("token", "group__name")
    readonly_fields = ("token", "times_used", "created_at")
