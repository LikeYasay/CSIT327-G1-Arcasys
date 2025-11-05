import datetime
import logging
import threading
from django.db import OperationalError, ProgrammingError
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from apps.events.models import Event, EventDepartment, EventLink, EventTag, Department, Tag
from .forms import AdminEditEventForm

# Set up logger
logger = logging.getLogger(__name__)


# Email sending functions (threaded)
def send_approval_email_async(user_email, user_name, login_url):
    """Send approval email in background thread"""
    try:
        html_message = render_to_string('events/account_approved.html', {
            'user_name': user_name,
            'login_url': login_url,
        })

        plain_message = f"""Arcasys System - Account Approved

Dear {user_name},

Your staff account has been approved.

You can now login to the system.

Login: {login_url}

This is an automated message from the Arcasys System."""

        send_mail(
            'Arcasys System - Account Approved',
            plain_message,
            'Arcasys System <arcasys.marketing.archive@gmail.com>',
            [user_email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Approval email sent successfully to {user_email}")
    except Exception as email_error:
        logger.error(f"Approval email failed for {user_email}: {str(email_error)}")

def send_rejection_email_async(user_email, user_name):
    """Send rejection email in background thread"""
    try:
        html_message = render_to_string('events/account_rejected.html', {
            'user_name': user_name,
        })

        plain_message = f"""Arcasys System - Application Status

Dear {user_name},

Your account application could not be approved at this time.

Please contact the system administrator if you have questions.

This is an automated message from the Arcasys System."""

        send_mail(
            'Arcasys System - Application Status',
            plain_message,
            'Arcasys System <arcasys.marketing.archive@gmail.com>',
            [user_email],
            html_message=html_message,
            fail_silently=False
        )
        logger.info(f"Rejection email sent successfully to {user_email}")
    except Exception as email_error:
        logger.error(f"Rejection email failed for {user_email}: {str(email_error)}")

# -----------------------------
# Events View - FOR ALL USERS
# -----------------------------
def events_view(request):
    from django.db.models import Q
    from datetime import datetime

    # Handle search functionality
    search_query = request.GET.get('q', '').strip()
    department_filter = request.GET.get('department', '')
    platform_filter = request.GET.get('platform', '')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    # Start with all events
    events = Event.objects.all().order_by('-EventDate')

    # EMPTY SEARCH VALIDATION
    if 'q' in request.GET and not search_query:
        messages.error(request, "Please enter a search term to find events.")
    elif search_query:
        # If there's a valid search query, filter events
        events = events.filter(
            Q(EventTitle__icontains=search_query) |
            Q(EventDescription__icontains=search_query) |
            Q(eventdepartment__DepartmentID__DepartmentName__icontains=search_query) |
            Q(eventtag__TagID__TagName__icontains=search_query)
        ).distinct()

    # Apply department filter
    if department_filter:
        events = events.filter(eventdepartment__DepartmentID=department_filter)

    # Apply platform filter
    if platform_filter:
        events = events.filter(eventlink__EventLinkName__icontains=platform_filter)

    # Apply date range filter
    if from_date:
        try:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            events = events.filter(EventDate__gte=from_date_obj)
        except ValueError:
            pass

    if to_date:
        try:
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            events = events.filter(EventDate__lte=to_date_obj)
        except ValueError:
            pass

    # Pagination
    paginator = Paginator(events, 10)
    page_number = request.GET.get('page')
    events_page = paginator.get_page(page_number)

    # Get unique departments and platforms for filters
    departments = Department.objects.all()

    # Get recent events for sidebar (last 10 created)
    recent_events = Event.objects.all().order_by('-EventCreatedAt')[:10]

    context = {
        'events': events_page,
        'search_query': search_query,
        'can_manage_events': request.user.is_authenticated and (request.user.isUserAdmin or request.user.isUserStaff),
        'is_admin': request.user.is_authenticated and request.user.isUserAdmin,
        'departments': departments,
        'recent_events': recent_events,
    }
    return render(request, "events/events.html", context)


def events_search_ajax(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        events = Event.objects.filter(
            Q(EventTitle__icontains=query) |
            Q(EventLocation__icontains=query)
        ).order_by('-EventDate')[:5]

        results = [
            {
                'id': str(e.EventID),
                'title': e.EventTitle,
                'date': e.EventDate.strftime('%b %d, %Y'),
                'location': e.EventLocation,
            }
            for e in events
        ]

    return JsonResponse({'results': results})


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
        title = (request.POST.get("event_title") or "").strip()
        department = (request.POST.get("office") or "").strip()
        event_date = (request.POST.get("event_date") or "").strip()
        event_time = (request.POST.get("event_time") or "").strip()
        location = (request.POST.get("location") or "").strip()
        description = (request.POST.get("description") or "").strip()
        tags_raw = (request.POST.get("tags_input") or "").strip()

        # Links (EventLink model)
        facebook_link = (request.POST.get("facebook_link") or "").strip()
        tiktok_link = (request.POST.get("tiktok_link") or "").strip()
        youtube_link = (request.POST.get("youtube_link") or "").strip()
        website_link = (request.POST.get("website_link") or "").strip()

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
            ("TikTok Link", tiktok_link),
            ("YouTube Link", youtube_link),
            ("Website Link", website_link),
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
def edit_event_view(request, EventID):
    # Check if user has permission to edit events
    if not request.user.isUserAdmin and not request.user.isUserStaff:
        messages.error(request, "Unauthorized access. Staff or admin privileges required.")
        return redirect("events:events")

    # Fetch event instance
    event = get_object_or_404(Event, pk=EventID)

    # Prepare initial form data from the event
    initial = {
        "event_title": event.EventTitle,
        "department": event.eventdepartment_set.first().DepartmentID if event.eventdepartment_set.exists() else None,
        "event_date": event.EventDate.strftime("%Y-%m-%d") if event.EventDate else "",
        "event_time": event.EventTime.strftime("%H:%M") if event.EventTime else "",
        "location": event.EventLocation,
        "description": event.EventDescription,
        "tags": ', '.join([tag.TagID.TagName for tag in event.eventtag_set.all()]),
    }

    # Social links (if exist)
    links = {link.EventLinkName.lower(): link.EventLinkURL for link in event.eventlink_set.all()}
    initial.update({
        "facebook": links.get("facebook", ""),
        "tiktok": links.get("tiktok", ""),
        "youtube": links.get("youtube", ""),
        "website": links.get("website", ""),
    })

    # MAM - 36
    if request.method == "POST":
        form = AdminEditEventForm(request.POST)
        if form.is_valid():
            # Handle saving manually since it's not a ModelForm
            event.EventTitle = form.cleaned_data["event_title"]
            event.EventLocation = form.cleaned_data["location"]
            event.EventDate = form.cleaned_data["event_date"]
            event.EventTime = form.cleaned_data["event_time"]
            event.EventDescription = form.cleaned_data["description"]
            event.EventUpdatedAt = timezone.now()
            event.save()

            department_instance = form.cleaned_data["department"]
            # Ensure the department relation always matches the current selection
            event.eventdepartment_set.all().delete()
            event.eventdepartment_set.create(DepartmentID=department_instance)

            # Tags
            event.eventtag_set.all().delete()
            tags_str = form.cleaned_data.get("tags", "")
            for tag_name in [t.strip() for t in tags_str.split(",") if t.strip()]:
                from .models import Tag
                tag_obj, _ = Tag.objects.get_or_create(TagName=tag_name)
                event.eventtag_set.create(TagID=tag_obj)

            # Links
            for name in ["facebook", "tiktok", "youtube", "website"]:
                url = form.cleaned_data.get(name)
                if url:
                    from .models import EventLink
                    link, _ = EventLink.objects.get_or_create(EventID=event, EventLinkName=name.capitalize())
                    link.EventLinkURL = url
                    link.save()
                else:
                    from .models import EventLink
                    EventLink.objects.filter(EventID=event, EventLinkName=name.capitalize()).delete()

            messages.success(request, f"Event updated successfully.")
            event.refresh_from_db()
            return redirect("events:edit_event", EventID=event.EventID)
        else:
            messages.error(request, f"Please fix the errors below.")
    else:
        form = AdminEditEventForm(initial=initial)

    # Departments for dropdown
    departments = Department.objects.all()

    context = {
        "form": form,
        "event": event,
        "departments": departments,
    }

    return render(request, "events/edit_event.html", context)


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
        return redirect("events:events")

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
# Approval/Reject Views - FIXED WITH THREADING
# -----------------------------
@login_required
def approve_application(request, user_id):
    from apps.users.models import User

    if not request.user.isUserAdmin and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect("events:events")

    try:
        user = User.objects.get(UserID=user_id, isUserActive=False, isUserStaff=True)
        user.isUserActive = True
        user.UserApprovedBy = request.user
        user.UserApprovedAt = timezone.now()
        user.save()

        # Start email in background thread
        login_url = request.build_absolute_uri("/users/login/")
        email_thread = threading.Thread(
            target=send_approval_email_async,
            args=(user.UserEmail, user.UserFullName, login_url)
        )
        email_thread.daemon = True
        email_thread.start()

        messages.success(request,
                         f"Account for {user.UserFullName} approved successfully. Approval email has been queued.")
        logger.info(f"User {user.UserFullName} approved successfully - email queued in background")

    except User.DoesNotExist:
        messages.error(request, "User not found or already approved.")
        logger.warning(f"User approval failed: User {user_id} not found or already approved")

    return redirect('events:admin_approval')


@login_required
def reject_application(request, user_id):
    from apps.users.models import User

    if not request.user.isUserAdmin and not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect("events:events")

    try:
        user = User.objects.get(UserID=user_id, isUserActive=False, isUserStaff=True)
        user_name = user.UserFullName
        user_email = user.UserEmail

        # Start email in background thread
        email_thread = threading.Thread(
            target=send_rejection_email_async,
            args=(user_email, user_name)
        )
        email_thread.daemon = True
        email_thread.start()

        # Delete user after queuing email
        user.delete()

        messages.success(request, f"Account for {user_name} rejected. Rejection email has been queued.")
        logger.info(f"User {user_name} rejected successfully - email queued in background")

    except User.DoesNotExist:
        messages.error(request, "User not found or already processed.")
        logger.warning(f"User rejection failed: User {user_id} not found or already processed")

    return redirect('events:admin_approval')