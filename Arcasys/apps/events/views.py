import datetime
from django.db import OperationalError, ProgrammingError
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime
from django.db import transaction
from django.shortcuts import render
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from apps.events.models import Event, EventDepartment, EventLink, EventTag, Department, Tag
from .forms import AdminEditEventForm

# -----------------------------
# Events View - FOR ALL USERS
# -----------------------------
def events_view(request):
    # Check permissions for conditional UI
    can_manage_events = request.user.is_authenticated and (request.user.isUserAdmin or request.user.isUserStaff)
    
    context = {
        'can_manage_events': can_manage_events,
        'is_admin': request.user.is_authenticated and request.user.isUserAdmin,
    }
    return render(request, "events/events.html", context)

# -----------------------------
# Add Event View - FOR STAFF & ADMIN
# -----------------------------
@login_required
def add_event_view(request):
    # Check if user has permission to add events
    if not request.user.isUserAdmin and not request.user.isUserStaff:
        messages.error(request, "Unauthorized access. Staff or admin privileges required.")
        return redirect("events:events")
    
    REDIRECT_URL_NAME = "events:add_event"
    
    if request.method == "POST":
        # 1) Collect data
        title       = (request.POST.get("event_title") or "").strip()
        department = (request.POST.get("office") or "").strip() 
        event_date  = (request.POST.get("event_date") or "").strip()
        event_time  = (request.POST.get("event_time") or "").strip()
        location    = (request.POST.get("location") or "").strip()
        description = (request.POST.get("description") or "").strip()
        tags_raw    = (request.POST.get("tags_input") or "").strip()

        # Links (EventLink model)
        facebook_link = (request.POST.get("facebook_link") or "").strip()
        tiktok_link   = (request.POST.get("tiktok_link") or "").strip()
        youtube_link  = (request.POST.get("youtube_link") or "").strip()
        website_link  = (request.POST.get("website_link") or "").strip()

        # MAM-29
        required = {
            "Event Title": title,
            "Office/Department": department,
            "Event Date": event_date,
            "Event Time": event_time,
            "Location": location,
            "Description": description,
        }
        for label, val in required.items():
            if not val:
                messages.error(request, f"{label} is required.")
                return redirect(REDIRECT_URL_NAME)

        # MAM-31
        try:
            d = datetime.strptime(event_date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format. Use YYYY-MM-DD.")
            return redirect(REDIRECT_URL_NAME)

        try:
            t = datetime.strptime(event_time, "%H:%M").time()
        except ValueError:
            messages.error(request, "Invalid time format. Use 24-hr HH:MM.")
            return redirect(REDIRECT_URL_NAME)

        # Links/URLs
        url_validator = URLValidator()
        link_data = [
            ("Facebook Link", facebook_link),
            ("TikTok Link",   tiktok_link),
            ("YouTube Link",  youtube_link),
            ("Website Link",  website_link),
        ]
        for label, url in link_data:
            if url:
                try:
                    url_validator(url)
                except ValidationError:
                    messages.error(request, f"{label} is not a valid URL.")
                    return redirect(REDIRECT_URL_NAME)

        # MAM-32
        department_obj = Department.objects.get(pk=department)
        try:
            dup = Event.objects.filter(
                EventTitle__iexact=title,
                EventDate=d,
                eventdepartment__DepartmentID=department_obj, 
            ).exists()
            
            if dup:
                messages.error(request, f"Event already exists.")
                return redirect(REDIRECT_URL_NAME)
        
        except (OperationalError, ProgrammingError, Exception) as e:
            messages.error(request, f"A database error occurred during duplicate check: {e}")
            return redirect(REDIRECT_URL_NAME)

        # Create event record
        try:
            with transaction.atomic():
                event = Event.objects.create(
                    EventTitle=title,
                    EventDate=d,
                    EventTime=t,
                    EventLocation=location,
                    EventDescription=description,
                )
                
                # Link the Department
                EventDepartment.objects.create(
                    EventID=event,
                    DepartmentID=department_obj 
                )

                # Tags 
                tag_names = _parse_tags(tags_raw)
                if tag_names:
                    for nm in tag_names:
                        tag_obj, created = Tag.objects.get_or_create(
                            TagName__iexact=nm, 
                            defaults={'TagName': nm}
                        )
                        EventTag.objects.create(EventID=event, TagID=tag_obj)

                # Links/URLs
                for link_name, link_url in link_data:
                    if link_url:
                        EventLink.objects.create(
                            EventID=event, 
                            EventLinkName=link_name.replace(" Link", ""), 
                            EventLinkURL=link_url
                        )

            messages.success(request, f"Event created successfully.")
            return redirect(REDIRECT_URL_NAME) 
        
        except Exception as e:
            messages.error(request, f"Could not create event: {e}")
            return redirect(REDIRECT_URL_NAME)

    context = {
        'departments': Department.objects.all(),
    }
    return render(request, "events/add_event.html", context)

# -----------------------------
# Edit Event View - FOR STAFF & ADMIN
# -----------------------------
@login_required
def edit_event_view(request):
    # Check if user has permission to edit events
    if not request.user.isUserAdmin and not request.user.isUserStaff:
        messages.error(request, "Unauthorized access. Staff or admin privileges required.")
        return redirect("events:events")
    
    # Normally you'd fetch an Event instance by ID and use its values for initial.
    initial = {
        "event_title": "Student Organizations Accreditation Ceremony",
        "department": "SSO",
        "event_date": "2025-09-05",
        "event_time": "09:10",
        "location": "CIT-U Auditorium",
        "description": (
            "Because we #LeadTheFuture, WATCH the Wildcat leadership SHINE as our student "
            "leaders from the different CIT-U accredited student organizations receive their "
            "accreditation confirmation in a symbolic ceremony. Go, Wildcats!"
        ),
        "facebook": "https://facebook.com/event-page",
        "tiktok": "https://tiktok.com/@event-post",
        "youtube": "https://youtube.com/watch?v=...",
        "website": "https://website.com/event-registration",
        "tags": "SSO, LeadTheFuture, Organizations",
    }

    if request.method == "POST":
        form = AdminEditEventForm(request.POST)
        if form.is_valid():
            # TODO: Persist to DB (update Event record)
            # e.g. Event.objects.filter(pk=event_id).update(**mapped_fields)
            messages.success(request, "Event updated successfully.")
            return redirect("events:edit_event")
        messages.error(request, "Please fix the errors below.")
    else:
        form = AdminEditEventForm(initial=initial)

    return render(request, "events/edit_event.html", {"form": form})

# Helper function for tags
def _parse_tags(raw: str):
    """Turn 'SDG, Workshop #Seminar' into unique tokens preserving case."""
    if not raw:
        return []
    parts = [p.lstrip("#").strip() for p in raw.replace(",", " ").split() if p.strip()]
    seen, out = set(), []
    for p in parts:
        k = p.lower()
        if k not in seen:
            out.append(p)
            seen.add(k)
    return out

# -----------------------------
# Admin Dashboard View
# -----------------------------
@login_required
def admin_approval_view(request):
    from apps.users.models import User
    
    if not request.user.isUserAdmin and not request.user.is_superuser:
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("events:events")  # FIXED: Changed from 'events:add_events' to 'events:events'
    
    pending_users = User.objects.filter(isUserActive=False, isUserStaff=True)
    applications = []
    for user in pending_users:
        applications.append({
            'id': user.UserID,
            'full_name': user.UserFullName,
            'email': user.UserEmail,
            'date_applied': user.UserCreatedAt.strftime('%Y-%m-%d')
        })
    
    return render(request, "events/admin_approval.html", {'applications': applications})

# -----------------------------
# Approval/Reject Views
# -----------------------------
@login_required
def approve_application(request, user_id):
    from apps.users.models import User
    
    if not request.user.isUserAdmin and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect("events:events")  # FIXED: Changed from 'events:add_events' to 'events:events'
    
    try:
        user = User.objects.get(UserID=user_id, isUserActive=False, isUserStaff=True)
        user.isUserActive = True
        user.UserApprovedBy = request.user
        user.UserApprovedAt = timezone.now()
        user.save()
        
        # Send approval email
        login_url = request.build_absolute_uri("/users/login/")
        
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
    
    return redirect('events:admin_approval')

@login_required
def reject_application(request, user_id):
    from apps.users.models import User
    
    if not request.user.isUserAdmin and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect("events:events")  # FIXED: Changed from 'events:add_events' to 'events:events'
    
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
    
    return redirect('events:admin_approval')