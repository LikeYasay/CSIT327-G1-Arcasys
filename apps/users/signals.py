from django.contrib.auth import user_logged_in
from django.dispatch import receiver
from django.utils import timezone

@receiver(user_logged_in)
def update_user_last_login(sender, request, user, **kwargs):
    """Update custom UserLastLogin field when user logs in"""
    user.UserLastLogin = timezone.now()
    user.save(update_fields=['UserLastLogin'])