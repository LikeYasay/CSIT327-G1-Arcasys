from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Return matching user(s) by email address - using UserEmail field"""
        active_users = User._default_manager.filter(
            UserEmail__iexact=email, 
            isUserActive=True  # Fixed field name
        )
        return (u for u in active_users if u.has_usable_password())