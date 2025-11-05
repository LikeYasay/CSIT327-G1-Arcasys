import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.urls import reverse_lazy
import re

from .models import User, Role
from apps.shared.email_utils import send_sendgrid_email  # ADD THIS IMPORT

# Set up logger
logger = logging.getLogger(__name__)


# -----------------------------
# Email Sending Functions - SENDGRID WEB API
# -----------------------------
def send_registration_email_async(email, first_name):
    """Send registration email using SendGrid Web API"""
    try:
        from django.core.mail import send_mail
        from django.conf import settings

        html_message = render_to_string('users/registration_notification.html', {'first_name': first_name})
        plain_message = f"""Arcasys System - Registration Received

Dear {first_name},

Your request for a staff account has been received.

Status: Pending Approval

The system administrator will review your application. You will receive a notification once your account has been approved.

This is an automated message from the Arcasys System.

Thank you."""

        # Use SendGrid Web API
        success = send_sendgrid_email(
            to_email=email,
            subject='Arcasys System - Registration Received',
            plain_message=plain_message,
            html_message=html_message
        )

        if success:
            logger.info(f"Registration email sent successfully to {email}")
        else:
            logger.error(f"Registration email failed for {email}")

        return success

    except Exception as email_error:
        logger.error(f"Registration email failed for {email}: {email_error}")
        return False


def send_password_reset_pending_email_async(user_email, user_name, registration_date):
    """Send pending account password reset email using SendGrid Web API"""
    try:
        html_message = render_to_string('users/pending_reset_email.html', {
            'user_name': user_name,
            'registration_date': registration_date,
        })

        plain_message = f"""Arcasys System - Password Reset

Dear {user_name},

A password reset was requested for your account.

Note: Your account registration from {registration_date} is pending approval. Password reset is available after approval.

This is an automated message from the Arcasys System."""

        # Use SendGrid Web API
        success = send_sendgrid_email(
            to_email=user_email,
            subject='Arcasys System - Password Reset',
            plain_message=plain_message,
            html_message=html_message
        )

        if success:
            logger.info(f"Pending reset email sent successfully to {user_email}")
        else:
            logger.error(f"Pending reset email failed for {user_email}")

        return success

    except Exception as email_error:
        logger.error(f"Pending reset email failed for {user_email}: {email_error}")
        return False


# -----------------------------
# Email Validation Helper Function
# -----------------------------
def is_valid_email(email):
    """
    Strict email validation - only allow specific domains
    """
    # Fixed regex pattern (was x0 instead of 0-9)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False

    domain = email.split('@')[1].lower()

    # ONLY allow these specific domains
    allowed_domains = [
        'gmail.com',
        'yahoo.com',
        'outlook.com',
        'hotmail.com',
        'icloud.com',
        'cit.edu',  # Your organization
    ]

    return domain in allowed_domains


# -----------------------------
# Login View
# -----------------------------
def login_view(request):
    if request.user.is_authenticated:
        if request.user.isUserAdmin or request.user.is_superuser:
            return redirect("events:admin_approval")
        else:
            return redirect("events:events")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        remember_me = request.POST.get("remember_me")

        # Store form data to repopulate on error
        form_data = {
            'email': email,
            'password': password,
        }
        clear_fields = {}
        field_errors = {}  # Track field-specific errors for inline display

        # A. Client-side validation: Invalid input format
        # 1. Check email format FIRST (most important)
        if email and not is_valid_email(email):
            field_errors['email'] = "Please enter a valid email address with proper domain (e.g., example@gmail.com)."
            # FORMAT ERROR: Keep both fields filled
            clear_fields['email'] = False  # Keep email
            clear_fields['password'] = True  # Keep password
            return render(request, "users/login.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

        # 2. Check if fields are empty (AFTER email format check)
        if not email:
            field_errors['email'] = "Please enter your email address."
            clear_fields['email'] = True
        if not password:
            field_errors['password'] = "Please enter your password."
            clear_fields['password'] = True

        if field_errors:
            # If any field errors exist, return immediately
            return render(request, "users/login.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

        # B. Server-side validation: Authentication errors
        # 3. Check if account exists (both active and pending)
        user_exists = False
        try:
            # Check for active account first
            active_user = User.objects.get(UserEmail__iexact=email, isUserActive=True)
            user_exists = True
        except User.DoesNotExist:
            # Check for pending account
            try:
                pending_user = User.objects.get(UserEmail__iexact=email, isUserActive=False, isUserStaff=True)
                user_exists = True
                # Account exists but is pending
                if pending_user.check_password(password):
                    messages.error(request,
                                   "Your account is pending administrator approval. Please wait for approval email.",
                                   extra_tags='auth_error')
                else:
                    # AUTH ERROR: Generic message, keep email, clear password
                    messages.error(request, "Invalid email or password.", extra_tags='auth_error')
                clear_fields['email'] = False  # Keep email
                clear_fields['password'] = True  # Clear password
                return render(request, "users/login.html", {
                    'form_data': form_data,
                    'clear_fields': clear_fields,
                    'field_errors': field_errors
                })
            except User.DoesNotExist:
                # No account found at all - AUTH ERROR
                messages.error(request, "Invalid email or password.", extra_tags='auth_error')
                clear_fields['email'] = False  # Keep email
                clear_fields['password'] = True  # Clear password
                return render(request, "users/login.html", {
                    'form_data': form_data,
                    'clear_fields': clear_fields,
                    'field_errors': field_errors
                })

        # 4. Authenticate with password (account exists and is active)
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)

            # Redirect based on role
            if user.isUserAdmin or user.is_superuser:
                response = redirect("events:admin_approval")
            else:
                response = redirect("events:events")

            # Remember Me
            if remember_me:
                response.set_cookie('remembered_email', email, max_age=30 * 24 * 60 * 60)
                response.set_cookie('remembered_password', password, max_age=30 * 24 * 60 * 60)
            else:
                response.delete_cookie('remembered_email')
                response.delete_cookie('remembered_password')

            return response
        else:
            # Password is incorrect but email exists - AUTH ERROR
            messages.error(request, "Invalid email or password.", extra_tags='auth_error')
            clear_fields['email'] = False  # Keep email
            clear_fields['password'] = True  # Clear only password
            return render(request, "users/login.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

    return render(request, "users/login.html")


# -----------------------------
# Register View - FIXED WITH SENDGRID WEB API
# -----------------------------
def register_view(request):
    if request.user.is_authenticated:
        if request.user.isUserAdmin or request.user.is_superuser:
            return redirect("events:admin_approval")
        else:
            return redirect("events:events")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # Store form data to repopulate on error
        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password,
            'confirm_password': confirm_password,
        }

        clear_fields = {}
        field_errors = {}  # Track field-specific errors for inline display

        # A. Client-side validation: Invalid input format
        # 1. Check email format FIRST
        if email and not is_valid_email(email):
            field_errors['email'] = "Please enter a valid email address with proper domain (e.g., example@gmail.com)."
            # FORMAT ERROR: Keep all fields filled
            clear_fields['email'] = False
            clear_fields['password'] = False
            clear_fields['confirm_password'] = False
            return render(request, "users/register.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

        # 2. Check if fields are empty (AFTER email format check)
        if not first_name:
            field_errors['first_name'] = "Please enter your first name."
            clear_fields['first_name'] = True
        if not last_name:
            field_errors['last_name'] = "Please enter your last name."
            clear_fields['last_name'] = True
        if not email:
            field_errors['email'] = "Please enter your email address."
            clear_fields['email'] = True
        if not password:
            field_errors['password'] = "Please enter your password."
            clear_fields['password'] = True
        if not confirm_password:
            field_errors['confirm_password'] = "Please confirm your password."
            clear_fields['confirm_password'] = True

        if field_errors:
            # If any field errors exist, return immediately
            return render(request, "users/register.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

        # C. Password strength validation (BEFORE checking match)
        password_errors = []
        try:
            validate_password(password)
        except DjangoValidationError as e:
            password_errors = list(e.messages)

        # Show password errors sequentially (only the first one)
        if password_errors:
            field_errors['password'] = password_errors[0]  # Show only the first error
            # Keep all fields filled for correction
            clear_fields['password'] = False
            clear_fields['confirm_password'] = False
            return render(request, "users/register.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

        # B. Password confirmation mismatch (AFTER password strength check)
        if password != confirm_password:
            field_errors['confirm_password'] = "Passwords do not match."
            # Keep all fields filled, don't clear anything
            clear_fields['password'] = False
            clear_fields['confirm_password'] = False
            return render(request, "users/register.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

        # D. Server-side validation: Existing user
        existing_user = User.objects.filter(UserEmail__iexact=email).first()
        if existing_user:
            if existing_user.isUserActive:
                messages.error(request, "Email already registered. Please login.", extra_tags='server_error')
            else:
                messages.error(request, "Email has pending application. Wait for approval.", extra_tags='server_error')
            # Clear email for security, keep names
            clear_fields['email'] = True
            clear_fields['password'] = True
            clear_fields['confirm_password'] = True
            return render(request, "users/register.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

        try:
            # Get or create the Staff role
            staff_role, created = Role.objects.get_or_create(
                RoleName='Staff'
            )

            # FIXED: Use the correct parameter names
            user = User.objects.create_user(
                UserEmail=email,
                UserFullName=f"{first_name} {last_name}".strip(),
                password=password,  # This is the correct parameter name
                RoleID=staff_role,
                isUserActive=False,
                isUserStaff=True
            )

            # Send registration email using SendGrid Web API (NO THREADING)
            send_registration_email_async(email, first_name)

            logger.info(f"User {first_name} {last_name} registered successfully - email sent via SendGrid API")

            return render(request, "users/registration_success.html", {
                'user_name': f"{first_name} {last_name}",
                'email': email
            })

        except Exception as e:
            logger.error(f"Registration error: {e}")
            messages.error(request, "Registration failed. Please try again.", extra_tags='server_error')
            return render(request, "users/register.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

    return render(request, "users/register.html")


# -----------------------------
# Logout View
# -----------------------------
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("users:login")
    return render(request, "users/logout.html")


# -----------------------------
# Custom Password Reset Form
# -----------------------------
class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Return matching active users only"""
        active_users = User._default_manager.filter(
            UserEmail__iexact=email,
            isUserActive=True
        )
        return (u for u in active_users if u.has_usable_password())


# -----------------------------
# Custom Set Password Form
# -----------------------------
class CustomSetPasswordForm(SetPasswordForm):
    def clean(self):
        cleaned_data = self.cleaned_data
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        # Clear ALL existing errors
        self._errors = {}

        # A. Password strength validation FIRST
        if new_password1:
            password_errors = []
            try:
                validate_password(new_password1, self.user)
            except DjangoValidationError as e:
                password_errors = list(e.messages)

            # Show only the first password error
            if password_errors:
                self.add_error('new_password1', password_errors[0])
                return cleaned_data

        # B. Password confirmation mismatch
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', "Passwords do not match.")
            return cleaned_data

        return cleaned_data

    def clean_new_password1(self):
        return self.cleaned_data.get('new_password1')

    def clean_new_password2(self):
        return self.cleaned_data.get('new_password2')


# -----------------------------
# Password Reset Views - FIXED WITH SENDGRID WEB API
# -----------------------------
class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        try:
            email = form.cleaned_data['email']

            # Check for pending accounts
            try:
                pending_user = User.objects.get(UserEmail__iexact=email, isUserActive=False, isUserStaff=True)

                # Send pending account email using SendGrid Web API (NO THREADING)
                send_password_reset_pending_email_async(
                    pending_user.UserEmail,
                    pending_user.UserFullName,
                    pending_user.UserCreatedAt.strftime('%B %d, %Y')
                )

                logger.info(f"Pending reset email sent via SendGrid API for {pending_user.UserEmail}")

                return self.render_success_response()

            except User.DoesNotExist:
                pass

            # For active users - proceed with normal password reset (Django handles this)
            return super().form_valid(form)

        except Exception as e:
            logger.error(f"Password reset error: {e}")
            messages.error(self.request, "An error occurred while processing your request. Please try again.")
            return self.form_invalid(form)

    def render_success_response(self):
        return render(self.request, 'users/password_reset_done.html')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')
    form_class = CustomSetPasswordForm

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'