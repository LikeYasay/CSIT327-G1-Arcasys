from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, 
    PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.auth.forms import PasswordResetForm
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from .models import User, Role

# -----------------------------
# Custom Password Reset Form - SIMPLIFIED
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
# Landing Page
# -----------------------------
def landing(request):
    return render(request, "ArcasysApp/landing.html")

# -----------------------------
# Login View - SIMPLIFIED
# -----------------------------
# -----------------------------
# Login View - UPDATED with Remember Me storing password
# -----------------------------
def login_view(request):
    if request.user.is_authenticated:
        if request.user.isUserAdmin or request.user.is_superuser:
            return redirect("admin_dashboard")
        else:
            return redirect("add_events")

    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        remember_me = request.POST.get("remember_me")

        # Basic validation
        if not email or not password:
            messages.error(request, "Email and password are required.")
            return render(request, "ArcasysApp/login.html")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "ArcasysApp/login.html")

        # Check for pending accounts first
        try:
            pending_user = User.objects.get(UserEmail__iexact=email, isUserActive=False, isUserStaff=True)
            if pending_user.check_password(password):
                messages.warning(request, "Your account is pending administrator approval. Please wait for approval email.")
            else:
                messages.error(request, "Invalid email or password.")
            return render(request, "ArcasysApp/login.html")
        except User.DoesNotExist:
            pass

        # Normal authentication for active users
        user = authenticate(request, UserEmail=email, password=password)

        if user is not None:
            if user.isUserStaff and not user.isUserActive:
                messages.warning(request, "Your account is pending administrator approval. Please wait for approval email.")
                return render(request, "ArcasysApp/login.html")
            
            login(request, user)

            # Redirect based on role
            if user.isUserAdmin or user.is_superuser:
                response = redirect("admin_dashboard")
            else:
                response = redirect("add_events")

            # Remember Me - STORE BOTH EMAIL AND PASSWORD
            if remember_me:
                response.set_cookie('remembered_email', email, max_age=30*24*60*60)  # 30 days
                response.set_cookie('remembered_password', password, max_age=30*24*60*60)  # 30 days
            else:
                response.delete_cookie('remembered_email')
                response.delete_cookie('remembered_password')

            return response
        else:
            messages.error(request, "Invalid email or password.")
            return render(request, "ArcasysApp/login.html")

    return render(request, "ArcasysApp/login.html")

# -----------------------------
# Register View - SIMPLIFIED
# -----------------------------
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

# -----------------------------
# Register View - UPDATED with Django's password validation
# -----------------------------
def register_view(request):
    if request.user.is_authenticated:
        if request.user.isUserAdmin or request.user.is_superuser:
            return redirect("admin_dashboard")
        else:
            return redirect("add_events")

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # Validation
        required_fields = {'First Name': first_name, 'Last Name': last_name, 'Email': email, 
                          'Password': password, 'Confirm Password': confirm_password}
        for field, value in required_fields.items():
            if not value:
                messages.error(request, f"{field} is required.")
                return render(request, "ArcasysApp/register.html")

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "ArcasysApp/register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "ArcasysApp/register.html")

        # Use Django's built-in password validation (same as password change)
        try:
            validate_password(password)
        except DjangoValidationError as e:
            # Convert Django's validation errors to messages
            for error in e:
                messages.error(request, error)
            return render(request, "ArcasysApp/register.html")

        # Check existing user
        existing_user = User.objects.filter(UserEmail=email).first()
        if existing_user:
            if existing_user.isUserActive:
                messages.error(request, "Email already registered. Please login.")
            else:
                messages.error(request, "Email has pending application. Wait for approval.")
            return render(request, "ArcasysApp/register.html")

        try:
            staff_role = Role.objects.get(RoleName='Staff')
            user = User.objects.create_user(
                UserEmail=email,
                UserFullName=f"{first_name} {last_name}".strip(),
                password=password,
                RoleID=staff_role,
                isUserActive=False,
                isUserStaff=True
            )

            # Send registration email
            html_message = render_to_string('ArcasysApp/registration_notification.html', {'first_name': first_name})
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

            return render(request, "ArcasysApp/registration_success.html", {
                'user_name': f"{first_name} {last_name}",
                'email': email
            })

        except Exception as e:
            messages.error(request, f"Registration error: {str(e)}")
            return render(request, "ArcasysApp/register.html")

    return render(request, "ArcasysApp/register.html")

# -----------------------------
# Logout View
# -----------------------------
def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")
    return render(request, "ArcasysApp/logout.html")

# -----------------------------
# Events & Contact Pages
# -----------------------------
def events_view(request):
    return render(request, "ArcasysApp/events.html")

def contact_view(request):
    return render(request, "ArcasysApp/contact.html")

# -----------------------------
# Admin Dashboard View
# -----------------------------
@login_required
def admin_dashboard_view(request):
    if not request.user.isUserAdmin and not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("add_events")
    
    pending_users = User.objects.filter(isUserActive=False, isUserStaff=True)
    applications = []
    for user in pending_users:
        applications.append({
            'id': user.UserID,
            'full_name': user.UserFullName,
            'email': user.UserEmail,
            'date_applied': user.UserCreatedAt.strftime('%Y-%m-%d')
        })
    
    return render(request, "ArcasysApp/admin_dashboard.html", {'applications': applications})

# -----------------------------
# Approval/Reject Views - SIMPLIFIED
# -----------------------------
@login_required
def approve_application(request, user_id):
    if not request.user.isUserAdmin and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect("add_events")
    
    try:
        user = User.objects.get(UserID=user_id, isUserActive=False, isUserStaff=True)
        user.isUserActive = True
        user.UserApprovedBy = request.user
        user.UserApprovedAt = timezone.now()
        user.save()
        
        # ✅ SEND APPROVAL EMAIL USING THE SPECIFIED TEMPLATE
        login_url = request.build_absolute_uri("/login/")
        
        html_message = render_to_string('ArcasysApp/account_approved.html', {
            'user_name': user.UserFullName,
            'login_url': login_url,
        })
        
        plain_message = f"""Hello {user.UserFullName},

Congratulations! Your Marketing Archive staff account has been approved.

You can now login to the system using your registered email and password.

LOGIN HERE: {login_url}

Next Steps:
• Use your registered email and password to login
• Access the event management system
• Start creating and managing events

If you have any questions, please contact the system administrator.

Best regards,
Marketing Archive Team"""

        send_mail(
            'Account Approved - Welcome to Marketing Archive!',
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.UserEmail],
            html_message=html_message,
            fail_silently=False,
        )
        
        messages.success(request, f"Account for {user.UserFullName} approved successfully. Approval email sent.")
    
    except User.DoesNotExist:
        messages.error(request, "User not found or already approved.")
    
    return redirect('admin_dashboard')

@login_required
def reject_application(request, user_id):
    if not request.user.isUserAdmin and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect("add_events")
    
    try:
        user = User.objects.get(UserID=user_id, isUserActive=False, isUserStaff=True)
        user_name = user.UserFullName
        user_email = user.UserEmail
        
        # ✅ SEND REJECTION EMAIL USING THE SPECIFIED TEMPLATE
        html_message = render_to_string('ArcasysApp/account_rejected.html', {
            'user_name': user_name,
        })
        
        plain_message = f"""Hello {user_name},

Unfortunately your account application has not been approved at this time.

You may contact the administrator if you have questions about this decision.

Best regards,
Marketing Archive Team"""

        send_mail(
            'Account Application Status - Marketing Archive',
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Delete user after sending email
        user.delete()
        messages.success(request, f"Account for {user_name} rejected. Rejection email sent.")
        
    except User.DoesNotExist:
        messages.error(request, "User not found or already processed.")
    
    return redirect('admin_dashboard')

# -----------------------------
# Add Events View
# -----------------------------
@login_required
def add_events_view(request):
    return render(request, "ArcasysApp/add_events.html")

# -----------------------------
# SIMPLIFIED Password Reset Views
# -----------------------------
class CustomPasswordResetView(PasswordResetView):
    template_name = 'ArcasysApp/password_reset.html'
    email_template_name = 'ArcasysApp/password_reset_email.html'
    subject_template_name = 'ArcasysApp/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    form_class = CustomPasswordResetForm

    def form_valid(self, form):
        email = form.cleaned_data['email']
        
        # Check for pending accounts
        try:
            pending_user = User.objects.get(UserEmail__iexact=email, isUserActive=False, isUserStaff=True)
            
            # Send pending account email instead of reset email
            html_message = render_to_string('ArcasysApp/pending_reset_email.html', {
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
            
            # Still show success page (security - don't reveal account status)
            return super().form_valid(form)
            
        except User.DoesNotExist:
            # No pending account found, proceed with normal password reset
            pass
        
        # Normal password reset for active accounts
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.email_template_name,
        }
        form.save(**opts)
        return super().form_valid(form)

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'ArcasysApp/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'ArcasysApp/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'ArcasysApp/password_reset_complete.html'
