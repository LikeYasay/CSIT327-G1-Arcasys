from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# -----------------------------
# Events View
# -----------------------------
def events_view(request):
    return render(request, "events/events.html")

# -----------------------------
# Add Events View
# -----------------------------
@login_required
def add_events_view(request):
    return render(request, "events/add_events.html")

# -----------------------------
# Admin Dashboard View
# -----------------------------
@login_required
def admin_dashboard_view(request):
    from ArcasysApp.models import User
    from django.utils import timezone
    
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
    
    return render(request, "events/admin_dashboard.html", {'applications': applications})

# -----------------------------
# Approval/Reject Views
# -----------------------------
@login_required
def approve_application(request, user_id):
    from ArcasysApp.models import User
    from django.core.mail import send_mail
    from django.conf import settings
    from django.template.loader import render_to_string
    from django.shortcuts import redirect
    
    if not request.user.isUserAdmin and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect("add_events")
    
    try:
        user = User.objects.get(UserID=user_id, isUserActive=False, isUserStaff=True)
        user.isUserActive = True
        user.UserApprovedBy = request.user
        user.UserApprovedAt = timezone.now()
        user.save()
        
        # Send approval email
        login_url = request.build_absolute_uri("/login/")
        
        html_message = render_to_string('events/account_approved.html', {
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
    from ArcasysApp.models import User
    from django.core.mail import send_mail
    from django.conf import settings
    from django.template.loader import render_to_string
    from django.shortcuts import redirect
    
    if not request.user.isUserAdmin and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect("add_events")
    
    try:
        user = User.objects.get(UserID=user_id, isUserActive=False, isUserStaff=True)
        user_name = user.UserFullName
        user_email = user.UserEmail
        
        # Send rejection email
        html_message = render_to_string('events/account_rejected.html', {
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