from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.validators import validate_email 
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
import random
import string
from .models import User, Role

# Custom Password Reset Form
class CustomPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Return matching user(s) by email address - using UserEmail field"""
        active_users = User._default_manager.filter(
            UserEmail__iexact=email, 
            isActive=True
        )
        return (u for u in active_users if u.has_usable_password())

def landing(request):
    return render(request, "ArcasysApp/landing.html")

def login_view(request):
    if request.user.is_authenticated:
        # If already logged in, redirect based on role
        if request.user.is_superuser or request.user.RoleID.RoleName == 'Admin':
            return redirect("/admin/")
        else:
            return redirect("events")
    
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        remember_me = request.POST.get("remember_me")  # Check if remember me is checked

        # User story: Empty field validation with specific messages
        if not email:
            messages.error(request, "Email is required.")
            return render(request, "ArcasysApp/login.html")
        if not password:
            messages.error(request, "Password is required.")
            return render(request, "ArcasysApp/login.html")

        # User story: Email format validation
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "ArcasysApp/login.html")

        # Authenticate using custom User model
        user = authenticate(request, UserEmail=email, password=password)

        if user is not None:
            login(request, user)
            
            # Handle remember me functionality
            response = redirect("events")  # Default redirect for regular users
            if user.is_superuser or user.RoleID.RoleName == 'Admin':
                response = redirect("/admin/")  # Redirect for admins
            
            # Set cookies if remember me is checked
            if remember_me:
                # Set cookies to expire in 30 days
                response.set_cookie('remembered_email', email, max_age=30*24*60*60)  # 30 days
                response.set_cookie('remembered_password', password, max_age=30*24*60*60)  # 30 days
            else:
                # Clear cookies if remember me is not checked
                response.delete_cookie('remembered_email')
                response.delete_cookie('remembered_password')
            
            return response
        else:
            # User story: Generic error for wrong credentials
            messages.error(request, "Invalid email or password.")
            return render(request, "ArcasysApp/login.html")

    return render(request, "ArcasysApp/login.html")

def register_view(request):
    if request.user.is_authenticated:
        # Redirect to appropriate page if already logged in
        if request.user.is_superuser or request.user.RoleID.RoleName == 'Admin':
            return redirect("/admin/")
        else:
            return redirect("events")
    
    if request.method == "POST":
        # Data retrieval - updated for custom User model
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        # Department field exists in form but we won't store it yet
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()
        
        # USER STORY: Check for empty fields FIRST with specific error messages
        if not first_name:
            messages.error(request, "First name is required.")
            return render(request, "ArcasysApp/register.html")
        if not last_name:
            messages.error(request, "Last name is required.")
            return render(request, "ArcasysApp/register.html")
        if not email:
            messages.error(request, "Email is required.")
            return render(request, "ArcasysApp/register.html")
        if not password:
            messages.error(request, "Password is required.")
            return render(request, "ArcasysApp/register.html")
        if not confirm_password:
            messages.error(request, "Please confirm your password.")
            return render(request, "ArcasysApp/register.html")

        # Concatenate first and last name for UserFullName
        user_full_name = f"{first_name} {last_name}".strip()
        
        # USER STORY: Email format validation with clear error
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, "Please enter a valid email address.")
            return render(request, "ArcasysApp/register.html")

        # USER STORY: Check for Password Match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "ArcasysApp/register.html")

        # USER STORY: Check password strength
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, "ArcasysApp/register.html")

        # USER STORY: Check if email already exists
        if User.objects.filter(UserEmail=email).exists():
            messages.error(request, "This email is already registered. Please use a different email or login.")
            return render(request, "ArcasysApp/register.html")

        # USER STORY: Generate and send verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        
        # Store verification data in session
        request.session['registration_data'] = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'password': password,
            'user_full_name': user_full_name,
            'verification_code': verification_code
        }
        request.session.set_expiry(600)  # 10 minutes expiration
        
        # Send verification email with HTML template
        try:
            # Render HTML email from template
            html_message = render_to_string('ArcasysApp/verification_email.html', {
                'first_name': first_name,
                'verification_code': verification_code,
            })
            
            # Plain text fallback
            plain_message = f"""Hello {first_name},

Your verification code is: {verification_code}

This code will expire in 10 minutes.

Best regards,
Marketing Archive Team"""
            
            send_mail(
                'Verify Your Marketing Archive Account',
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            return redirect('verify_email')
        except Exception as e:
            messages.error(request, "Failed to send verification email. Please try again.")
            return render(request, "ArcasysApp/register.html")

    return render(request, "ArcasysApp/register.html")

def verify_email_view(request):
    if 'registration_data' not in request.session:
        messages.error(request, "Registration session expired. Please start over.")
        return redirect('register')
    
    if request.method == "POST":
        entered_code = request.POST.get("verification_code")
        stored_data = request.session.get('registration_data')
        
        if entered_code == stored_data['verification_code']:
            # Code is correct, create the user
            try:
                user = User.objects.create_user(
                    UserEmail=stored_data['email'],
                    UserFullName=stored_data['user_full_name'],
                    password=stored_data['password']
                )
                
                # Clear session data
                del request.session['registration_data']
                
                messages.success(request, "Account created successfully! Please log in.")
                return redirect('login')
            except Exception as e:
                messages.error(request, "An error occurred during registration. Please try again.")
                return redirect('register')
        else:
            messages.error(request, "Invalid verification code. Please try again.")
    
    # Get the email from session to show user
    stored_data = request.session.get('registration_data', {})
    email = stored_data.get('email', '')
    
    return render(request, "ArcasysApp/verify_email.html", {'email': email})

def logout_view(request):
    if request.method == "POST":
        # Handle the POST request from the logout form
        logout(request)
        # Redirect to login page but DO NOT clear remember me cookies
        return redirect("login")  # Cookies persist after logout
    else:
        # Handle GET request - show the logout confirmation modal
        return render(request, "ArcasysApp/logout.html")

def events_view(request):
    return render(request, "ArcasysApp/events.html")

def contact_view(request):
    return render(request, "ArcasysApp/contact.html")

# Password Reset Views (Custom Django Auth)
class CustomPasswordResetView(PasswordResetView):
    template_name = 'ArcasysApp/password_reset.html'
    email_template_name = 'ArcasysApp/password_reset_email.html'
    subject_template_name = 'ArcasysApp/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    form_class = CustomPasswordResetForm  # Use the custom form
    
    # ADDED: Force HTML email
    def form_valid(self, form):
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': settings.DEFAULT_FROM_EMAIL,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.email_template_name,  # This forces HTML
            'extra_email_context': self.extra_email_context,
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

# Direct view functions for template preview
def view_password_reset(request):
    """Direct view for password reset form"""
    return render(request, "ArcasysApp/password_reset.html")

def view_password_reset_done(request):
    """Direct view for password reset done page"""
    return render(request, "ArcasysApp/password_reset_done.html")

def view_password_reset_confirm(request):
    """Direct view for password reset confirm page"""
    return render(request, "ArcasysApp/password_reset_confirm.html")

def view_password_reset_complete(request):
    """Direct view for password reset complete page"""
    return render(request, "ArcasysApp/password_reset_complete.html")