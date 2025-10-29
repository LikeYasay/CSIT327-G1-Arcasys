from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
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

# -----------------------------
# Email Validation Helper Function
# -----------------------------
def is_valid_email(email):
    """
    Strict email validation - only allow specific domains
    """
    # Basic email regex pattern
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
        # Add other specific domains you want to allow
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
            clear_fields['email'] = False    # Keep email
            clear_fields['password'] = True # Keep password
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
                    messages.error(request, "Your account is pending administrator approval. Please wait for approval email.", extra_tags='auth_error')
                else:
                    # AUTH ERROR: Generic message, keep email, clear password
                    messages.error(request, "Invalid email or password.", extra_tags='auth_error')
                clear_fields['email'] = False    # Keep email
                clear_fields['password'] = True  # Clear password
                return render(request, "users/login.html", {
                    'form_data': form_data,
                    'clear_fields': clear_fields,
                    'field_errors': field_errors
                })
            except User.DoesNotExist:
                # No account found at all - AUTH ERROR
                messages.error(request, "Invalid email or password.", extra_tags='auth_error')
                clear_fields['email'] = False    # Keep email
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
                response.set_cookie('remembered_email', email, max_age=30*24*60*60)
                response.set_cookie('remembered_password', password, max_age=30*24*60*60)
            else:
                response.delete_cookie('remembered_email')
                response.delete_cookie('remembered_password')

            return response
        else:
            # Password is incorrect but email exists - AUTH ERROR
            messages.error(request, "Invalid email or password.", extra_tags='auth_error')
            clear_fields['email'] = False    # Keep email
            clear_fields['password'] = True  # Clear only password
            return render(request, "users/login.html", {
                'form_data': form_data,
                'clear_fields': clear_fields,
                'field_errors': field_errors
            })

    return render(request, "users/login.html")

# -----------------------------
# Register View
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
           staff_role, created = Role.objects.get_or_create(RoleName='Staff')
            user = User.objects.create_user(
                UserEmail=email,
                UserFullName=f"{first_name} {last_name}".strip(),
                password=password,
                RoleID=staff_role,
                isUserActive=False,
                isUserStaff=True
            )

            # Send registration email
            html_message = render_to_string('users/registration_notification.html', {'first_name': first_name})
            plain_message = f"""Hello {first_name},

Your staff account has been created successfully and is pending administrator approval.

You will receive another email once your account has been approved.

Best regards,
Marketing Archive Team"""

            send_mail(
                'Account Registration Received - Marketing Archive',
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
                fail_silently=False,
            )

            return render(request, "users/registration_success.html", {
                'user_name': f"{first_name} {last_name}",
                'email': email
            })

        except Exception as e:
            messages.error(request, f"Registration error: {str(e)}", extra_tags='server_error')
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
# Custom Set Password Form for Clean Validation (EXACTLY like register view)
# -----------------------------
class CustomSetPasswordForm(SetPasswordForm):
    def clean(self):
        # Don't call super().clean() at all - we handle everything
        cleaned_data = self.cleaned_data
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")
        
        # Clear ALL existing errors
        self._errors = {}
        
        # A. Password strength validation FIRST (like register view)
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

        # B. Password confirmation mismatch (ONLY if password is valid)
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', "Passwords do not match.")
            return cleaned_data
        
        # If we get here, validation passed
        return cleaned_data

    # Override the default validation methods to prevent duplicate checks
    def clean_new_password1(self):
        return self.cleaned_data.get('new_password1')

    def clean_new_password2(self):
        return self.cleaned_data.get('new_password2')

# -----------------------------
# Password Reset Views
# -----------------------------
class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        email = form.cleaned_data['email']
        
        # Check for pending accounts
        try:
            pending_user = User.objects.get(UserEmail__iexact=email, isUserActive=False, isUserStaff=True)
            
            # Send pending account email
            html_message = render_to_string('users/pending_reset_email.html', {
                'user_name': pending_user.UserFullName,
                'registration_date': pending_user.UserCreatedAt.strftime('%B %d, %Y'),
            })
            
            plain_message = f"""Hello {pending_user.UserFullName},

You requested a password reset for your Marketing Archive staff account.

ACCOUNT STATUS: PENDING APPROVAL
Your account is still waiting for administrator approval. You cannot reset your password until your account is approved.

Your account registration was received on {pending_user.UserCreatedAt.strftime('%B %d, %Y')} and is currently awaiting administrator approval.

Once your account is approved, you will receive an approval email and will be able to use the regular password reset feature.

Please try again after your account has been approved.

Best regards,
Marketing Archive Team"""

            send_mail(
                'Password Reset Request - Pending Account - Marketing Archive',
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [pending_user.UserEmail],
                html_message=html_message,
                fail_silently=False,
            )
            
            return self.render_success_response()
            
        except User.DoesNotExist:
            pass
        
        # For active users - send HTML email only
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        
        users = form.get_users(email)
        for user in users:
            context = {
                'email': user.UserEmail,
                'domain': self.request.get_host(),
                'site_name': 'Marketing Archive',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': default_token_generator.make_token(user),
                'protocol': 'https' if self.request.is_secure() else 'http',
            }
            
            subject = 'Password Reset Request - Marketing Archive'
            html_message = render_to_string('users/password_reset_email.html', context)
            
            send_mail(
                subject,
                'Please view this email in HTML format.',
                settings.DEFAULT_FROM_EMAIL,
                [user.UserEmail],
                html_message=html_message,
                fail_silently=False,
            )
        
        return self.render_success_response()

    def render_success_response(self):
        """Render the success page without triggering default email sending"""
        return render(self.request, 'users/password_reset_done.html')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')
    form_class = CustomSetPasswordForm  # Use our custom form with clean validation

    def form_invalid(self, form):
        # This ensures our custom form errors are displayed properly
        return self.render_to_response(self.get_context_data(form=form))

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'