"""
OmniLab AI - Groups Service Layer
Handles group invitations, validation, and atomic student enrollment.
"""
import secrets
import logging
from datetime import timedelta
from typing import Tuple, Optional
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import Group, GroupInvitation, GroupMembership

logger = logging.getLogger(__name__)


class InviteTokenError(Exception):
    pass


class GroupService:
    """Business logic for mentorship groups and invitation links."""

    @staticmethod
    @transaction.atomic
    def generate_invite(
        group: Group,
        creator,
        expires_in_days: int = 7,
        max_uses: int = 0,
    ) -> GroupInvitation:
        """
        Creates a new cryptographically secure invitation token for the group.
        """
        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(days=max(1, expires_in_days))

        invitation = GroupInvitation.objects.create(
            group=group,
            token=token,
            created_by=creator,
            expires_at=expires_at,
            max_uses=max(0, max_uses),
            times_used=0,
            is_active=True,
        )
        logger.info(
            "Invite token generated: group=%s token=%s by=%s",
            group.name, token[:8], creator.email,
        )
        return invitation

    @staticmethod
    def validate_invite(token_str: str) -> Tuple[bool, str, Optional[GroupInvitation]]:
        """
        Validates invitation token.
        Returns (is_valid, message, invitation_or_None).
        """
        if not token_str:
            return False, "Taklif tokeni ko'rsatilmadi.", None

        try:
            invitation = GroupInvitation.objects.select_related("group", "group__mentor").get(
                token=token_str
            )
        except GroupInvitation.DoesNotExist:
            return False, "Yaroqsiz taklif havolasi.", None

        if not invitation.is_active:
            return False, "Ushbu taklif havolasi bekor qilingan.", None

        if invitation.is_expired:
            return False, "Taklif havolasining amal qilish muddati tugagan.", None

        if invitation.max_uses > 0 and invitation.times_used >= invitation.max_uses:
            return False, "Ushbu havola orqali ruxsat etilgan maksimal a'zolar soni to'lgan.", None

        if not invitation.group.is_active:
            return False, "Ushbu guruh hozirda faol emas.", None

        return True, "Yaroqli taklifnoma.", invitation

    @staticmethod
    @transaction.atomic
    def join_group_with_token(user, token_str: str) -> Tuple[bool, str, Optional[Group]]:
        """
        Enrolls authenticated student into the group using the token.
        Atomically increments times_used on the invitation.
        """
        is_valid, message, invitation = GroupService.validate_invite(token_str)
        if not is_valid or not invitation:
            return False, message, None

        group = invitation.group

        # Check if already a member
        membership, created = GroupMembership.objects.get_or_create(
            group=group,
            student=user,
            defaults={"status": GroupMembership.MembershipStatus.ACTIVE},
        )

        if not created:
            if membership.status != GroupMembership.MembershipStatus.ACTIVE:
                membership.status = GroupMembership.MembershipStatus.ACTIVE
                membership.save(update_fields=["status"])
                return True, f"Siz '{group.name}' guruhidagi a'zoligingizni qayta tikladingiz!", group
            return True, f"Siz allaqachon '{group.name}' guruhi a'zosisiz.", group

        # Increment invitation use count atomically
        GroupInvitation.objects.filter(pk=invitation.pk).update(
            times_used=F("times_used") + 1
        )

        logger.info(
            "Student %s joined group %s via token %s",
            user.email, group.name, token_str[:8],
        )
        return True, f"'{group.name}' guruhiga muvaffaqiyatli qo'shildingiz!", group
