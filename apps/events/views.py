import datetime
import logging
import traceback
import boto3
import os
import csv
import json
import tempfile
import subprocess
import re
import uuid
import platform
from django.urls import reverse
from django.db import OperationalError, ProgrammingError
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.template.loader import render_to_string
from datetime import datetime
from django.db import transaction
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from apps.events.backup_script import backup_database
from apps.events.models import BackupHistory, Event, EventDepartment, EventLink, EventTag, Department, RestoreOperation, \
    Tag, BackupHistory
from project import settings
from .forms import AdminEditEventForm
from apps.shared.email_utils import send_sendgrid_email
from django.conf import settings
from django.views.decorators.http import require_POST, require_GET

# Set up logger
logger = logging.getLogger(__name__)


def get_platform_config():
    """Get platform-specific configuration"""
    IS_RENDER = os.environ.get('RENDER', 'false').lower() == 'true'
    IS_WINDOWS = platform.system().lower() == 'windows'

    if IS_RENDER:
        return {
            'psql_path': 'psql',
            'pg_dump_path': 'pg_dump',
            'platform': 'render'
        }
    elif IS_WINDOWS:
        return {
            'psql_path': r"C:\Program Files\PostgreSQL\18\bin\psql.exe",
            'pg_dump_path': r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
            'platform': 'windows'
        }
    else:
        return {
            'psql_path': 'psql',
            'pg_dump_path': 'pg_dump',
            'platform': 'linux'
        }


# Email sending functions - SENDGRID WEB API
def send_approval_email_async(user_email, user_name, login_url):
    """Send approval email using SendGrid Web API"""
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

        # Use SendGrid Web API
        success = send_sendgrid_email(
            to_email=user_email,
            subject='Arcasys System - Account Approved',
            plain_message=plain_message,
            html_message=html_message
        )

        if success:
            logger.info(f"Approval email sent successfully to {user_email}")
        else:
            logger.error(f"Approval email failed for {user_email}")

        return success

    except Exception as email_error:
        logger.error(f"Approval email failed for {user_email}: {str(email_error)}")
        return False


def send_rejection_email_async(user_email, user_name):
    """Send rejection email using SendGrid Web API"""
    try:
        html_message = render_to_string('events/account_rejected.html', {
            'user_name': user_name,
        })

        plain_message = f"""Arcasys System - Application Status

Dear {user_name},

Your account application could not be approved at this time.

Please contact the system administrator if you have questions.

This is an automated message from the Arcasys System."""

        # Use SendGrid Web API
        success = send_sendgrid_email(
            to_email=user_email,
            subject='Arcasys System - Application Status',
            plain_message=plain_message,
            html_message=html_message
        )

        if success:
            logger.info(f"Rejection email sent successfully to {user_email}")
        else:
            logger.error(f"Rejection email failed for {user_email}")

        return success

    except Exception as email_error:
        logger.error(f"Rejection email failed for {user_email}: {str(email_error)}")
        return False


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


@login_required
def backup_history_view(request):
    backups = BackupHistory.objects.all().order_by('-BackupTimestamp')

    #  Filters -----
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').lower()

    if search_query:
        backups = backups.filter(Q(BackupName__icontains=search_query))

    if status_filter:
        if status_filter == "completed":
            backups = backups.filter(BackupStatus='completed')
        elif status_filter == "failed":
            backups = backups.filter(BackupStatus='failed')

    # Pagination -----
    paginator = Paginator(backups, 10)  # Show 10 backups per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Actions -----
    action = request.GET.get('action')
    backup_id = request.GET.get('id')

    if action and backup_id:
        if action == "download":
            return redirect('download_backup', id=backup_id)

        elif action == "view-log":
            backup = BackupHistory.objects.filter(BackupHistoryID=backup_id).first()
            if backup and backup.BackupLogFile and os.path.exists(backup.BackupLogFile.path):
                with open(backup.BackupLogFile.path, 'r') as f:
                    return HttpResponse(
                        f"<pre style='padding:1rem; background:#f4f4f4; border-radius:6px;'>{f.read()}</pre>"
                    )
            messages.error(request, "Log file not found.")
            return redirect('backup_history')

    # Delete Backup -----
    if request.method == "POST" and "delete_id" in request.POST:
        backup = BackupHistory.objects.filter(BackupHistoryID=request.POST["delete_id"]).first()
        if backup:
            if backup.BackupFile:
                backup.BackupFile.delete()
            if backup.BackupLogFile:
                backup.BackupLogFile.delete()
            backup.delete()
            messages.success(request, "Backup deleted successfully.")
        else:
            messages.error(request, "Backup not found.")
        return redirect('events:backup_history')

    # Export CSV -----
    if request.GET.get('export') == '1':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="Arcasys_Backups.csv"'

        writer = csv.writer(response)
        writer.writerow(['Backup Name', 'Status', 'Timestamp', 'Size', 'Backup File', 'Log File'])

        for backup in backups:
            backup_file_url = ""
            log_file_url = ""

            if backup.BackupFile:
                backup_file_url = request.build_absolute_uri(
                    reverse("events:download_backup", args=[backup.BackupHistoryID]) + "?file_type=backup"
                )
            if backup.BackupLogFile:
                log_file_url = request.build_absolute_uri(
                    reverse("events:download_backup", args=[backup.BackupHistoryID]) + "?file_type=log"
                )

            writer.writerow([
                backup.BackupName,
                backup.BackupStatus.capitalize(),
                backup.BackupTimestamp.strftime('%Y-%m-%d %H:%M:%S'),
                backup.BackupSize,
                backup_file_url,
                log_file_url,
            ])

        return response

    return render(request, 'events/backup_history.html', {
        "backups": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "nav_active": 'backup_management',
    })


@login_required
def backup_dashboard_view(request):
    recent_jobs = BackupHistory.objects.order_by('-BackupTimestamp')[:5]
    total_backups = BackupHistory.objects.count()
    successful_backups = BackupHistory.objects.filter(
        BackupStatus='completed',
        BackupTimestamp__gte=timezone.now() - timezone.timedelta(days=1)
    ).count()
    failed_backups = BackupHistory.objects.filter(BackupStatus='failed').count()

    # Generate alerts based on failed or recent backups
    alerts = []
    failed_jobs = BackupHistory.objects.filter(BackupStatus='failed').order_by('-BackupTimestamp')[:5]

    for job in failed_jobs:
        alerts.append({
            'Level': 'Critical',  # you can customize based on logic
            'Message': f"Backup '{job.BackupName}' failed.",
            'CreatedAt': job.BackupTimestamp,
            'RelatedBackup': job
        })

    context = {
        'recent_jobs': recent_jobs,
        'total_backups': total_backups,
        'successful_backups': successful_backups,
        'failed_backups': failed_backups,
        'alerts': alerts
    }
    return render(request, 'events/backup_dashboard.html', context)


@login_required
def restore_operations_view(request):
    """Display restore operations page"""
    backups = BackupHistory.objects.filter(BackupStatus='completed').order_by('-BackupTimestamp')

    paginator = Paginator(backups, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'backups': page_obj,
        "nav_active": 'backup_management',
    }

    return render(request, 'events/restore_operations.html', context)


# -----------------------------
# Backup Actions
# -----------------------------
def run_backup(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    try:
        backup_database()
        return JsonResponse({"status": "success", "message": "Backup completed successfully!"})
    except Exception as e:
        logger.error(f"Backup failed: {str(e)}")
        return JsonResponse({"status": "error", "message": f"Backup failed: {str(e)}"})


def download_backup(request, id):
    file_type = request.GET.get("file_type", "backup")
    backup = get_object_or_404(BackupHistory, BackupHistoryID=id)

    s3_key = getattr(backup, "BackupFile" if file_type == "backup" else "BackupLogFile", None)
    if not s3_key:
        raise Http404(f"{file_type.capitalize()} file not available.")

    s3_key = str(s3_key)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    presigned_url = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": s3_key
        },
        ExpiresIn=60
    )

    return HttpResponseRedirect(presigned_url)


def view_log(request, backup_id):
    try:
        backup = BackupHistory.objects.get(BackupHistoryID=backup_id)

        if not backup.BackupLogFile:
            return JsonResponse({
                'success': False,
                'message': 'No log file associated with this backup'
            })

        # Get the S3 file key (path in S3)
        file_key = backup.BackupLogFile.name

        # Read directly from S3 using boto3
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            response = s3_client.get_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_key
            )

            # Read and decode the content
            log_content = response['Body'].read().decode('utf-8', errors='ignore')

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error reading file from S3: {str(e)}'
            })

        return JsonResponse({
            'success': True,
            'content': log_content
        })

    except BackupHistory.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Backup record not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


# -----------------------------
# Approval/Reject Views - FIXED WITH SENDGRID WEB API
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

        # Send approval email using SendGrid Web API (NO THREADING)
        login_url = request.build_absolute_uri("/users/login/")
        send_approval_email_async(user.UserEmail, user.UserFullName, login_url)

        messages.success(request,
                         f"Account for {user.UserFullName} approved successfully. Approval email has been sent.")
        logger.info(f"User {user.UserFullName} approved successfully - email sent via SendGrid API")

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

        # Send rejection email using SendGrid Web API (NO THREADING)
        send_rejection_email_async(user_email, user_name)

        # Delete user after sending email
        user.delete()

        messages.success(request, f"Account for {user_name} rejected. Rejection email has been sent.")
        logger.info(f"User {user_name} rejected successfully - email sent via SendGrid API")

    except User.DoesNotExist:
        messages.error(request, "User not found or already processed.")
        logger.warning(f"User rejection failed: User {user_id} not found or already processed")

    return redirect('events:admin_approval')


@login_required
@require_POST
def restore_full_database(request):
    """
    Initiates full database restoration, including User and Role tables.
    Sessions and system tables are preserved.
    """
    try:
        data = json.loads(request.body)
        backup_id = data.get('backup_id')

        if not backup_id:
            return JsonResponse({'status': 'error', 'message': 'Backup ID is required'})

        # Get backup record
        backup = BackupHistory.objects.get(
            BackupHistoryID=backup_id,
            BackupStatus='completed'
        )

        # Create restore operation record
        restore_op, _ = RestoreOperation.objects.get_or_create(
            RestoreID=str(uuid.uuid4()),  # Ensure unique
            defaults={
                'RestoreStatus': 'in_progress',
                'RestoreProgress': 0,
                'RestoreMessage': 'Starting full restoration process...',
                'RestoreStartedAt': timezone.now(),
                'BackupHistoryID': backup
            }
        )

        # Execute restoration in background thread
        import threading
        thread = threading.Thread(
            target=execute_full_restoration_async,
            args=(str(backup.BackupFile), str(restore_op.RestoreID))
        )
        thread.daemon = True
        thread.start()

        return JsonResponse({
            'status': 'success',
            'message': 'Full restoration process started',
            'restore_op_id': str(restore_op.RestoreID)
        })

    except BackupHistory.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Backup not found'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Failed to start restoration: {str(e)}'})


def execute_full_restoration_async(backup_s3_key, restore_op_id):
    """
    Background restoration process.
    """
    from django.db import connection
    connection.close()

    try:
        restore_op = RestoreOperation.objects.get(RestoreID=restore_op_id)

        restore_op.RestoreProgress = 10
        restore_op.RestoreMessage = 'Downloading backup file...'
        restore_op.save()

        # Download and restore
        success = restore_full_database_from_s3(backup_s3_key, restore_op)

        # Update status
        restore_op = RestoreOperation.objects.get(RestoreID=restore_op_id)
        restore_op.RestoreStatus = 'completed' if success else 'failed'
        restore_op.RestoreProgress = 100
        restore_op.RestoreMessage = 'FULL DATA RESTORATION COMPLETED' if success else 'RESTORATION FAILED'
        restore_op.RestoreCompletedAt = timezone.now()
        restore_op.save()

    except Exception as e:
        try:
            restore_op = RestoreOperation.objects.get(RestoreID=restore_op_id)
            restore_op.RestoreStatus = 'failed'
            restore_op.RestoreMessage = f'Restoration failed: {str(e)}'
            restore_op.RestoreCompletedAt = timezone.now()
            restore_op.save()
        except RestoreOperation.DoesNotExist:
            logger.error(f"RestoreOperation {restore_op_id} not found during error handling")


def restore_full_database_from_s3(backup_s3_key, restore_op=None):
    """
    Downloads the backup from S3 and executes full restoration.
    """
    try:
        if restore_op:
            restore_op.RestoreProgress = 20
            restore_op.RestoreMessage = 'Processing backup file...'
            restore_op.save()

        # Download backup from S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        with tempfile.NamedTemporaryFile(suffix='.sql', delete=False) as temp_file:
            s3_client.download_fileobj(
                settings.AWS_STORAGE_BUCKET_NAME,
                backup_s3_key,
                temp_file
            )
            temp_file_path = temp_file.name

        # Execute restoration
        success = execute_full_restoration(temp_file_path, restore_op)

        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        return success

    except Exception as e:
        if restore_op:
            restore_op.RestoreStatus = 'failed'
            restore_op.RestoreMessage = f'Download failed: {str(e)}'
            restore_op.RestoreCompletedAt = timezone.now()
            restore_op.save()
        return False


def execute_full_restoration(sql_file_path, restore_op=None):
    """
    Actual restoration using psql - platform aware
    """
    try:
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')

        # Get platform config
        config = get_platform_config()
        psql_path = config['psql_path']

        env = os.environ.copy()

        # Handle password based on platform
        IS_RENDER = os.environ.get('RENDER', 'false').lower() == 'true'
        if not IS_RENDER:
            env['PGPASSWORD'] = db_password

        if restore_op:
            restore_op.RestoreProgress = 30
            restore_op.RestoreMessage = f'Preparing database for restoration on {config["platform"]}...'
            restore_op.save()

        # Build connection command based on platform
        if IS_RENDER:
            # Render connection string includes password
            base_cmd = [
                psql_path,
                f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
            ]
        else:
            # Local connection uses separate parameters
            base_cmd = [
                psql_path, '-h', db_host, '-p', db_port, '-U', db_user, '-d', db_name
            ]

        # Disable constraints
        disable_result = subprocess.run(
            base_cmd + ['-c', "SET session_replication_role = 'replica';", '--quiet'],
            env=env, capture_output=True, text=True
        )

        if disable_result.returncode != 0:
            logger.error(f"Failed to disable constraints: {disable_result.stderr}")
            if restore_op:
                restore_op.RestoreMessage = f'Failed to prepare database: {disable_result.stderr[:200]}'
                restore_op.save()
            return False

        if restore_op:
            restore_op.RestoreProgress = 40
            restore_op.RestoreMessage = 'Cleaning existing data...'
            restore_op.save()

        # Delete application tables but preserve django_session
        delete_script = """
        DELETE FROM public."EventTag";
        DELETE FROM public."EventDepartment";
        DELETE FROM public."EventLink";
        DELETE FROM public."Event";
        DELETE FROM public."Tag";
        DELETE FROM public."Department";
        DELETE FROM public."User";
        DELETE FROM public."Role";
        -- KEEP django_session table untouched
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as tmp_del:
            tmp_del.write(delete_script)
            tmp_del_path = tmp_del.name

        delete_result = subprocess.run(
            base_cmd + ['-f', tmp_del_path, '--quiet'],
            env=env, capture_output=True, text=True
        )

        os.unlink(tmp_del_path)

        if delete_result.returncode != 0:
            logger.error(f"Failed to clean tables: {delete_result.stderr}")
            if restore_op:
                restore_op.RestoreMessage = f'Failed to clean existing data: {delete_result.stderr[:200]}'
                restore_op.save()
            return False

        if restore_op:
            restore_op.RestoreProgress = 60
            restore_op.RestoreMessage = 'Processing backup data...'
            restore_op.save()

        # Read the backup SQL
        with open(sql_file_path, 'r', encoding='utf-8', errors='ignore') as f:
            sql_content = f.read()

        # Make inserts for BackupHistory idempotent
        sql_content = re.sub(
            r'INSERT INTO public\."BackupHistory"\s*\((.*?)\)\s*VALUES\s*\((.*?)\);',
            r'INSERT INTO public."BackupHistory" (\1) VALUES (\2) '
            r'ON CONFLICT ("BackupHistoryID") DO NOTHING;',
            sql_content,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Make inserts for RestoreOperation idempotent
        sql_content = re.sub(
            r'INSERT INTO public\."RestoreOperation"\s*\((.*?)\)\s*VALUES\s*\((.*?)\);',
            r'INSERT INTO public."RestoreOperation" (\1) VALUES (\2) '
            r'ON CONFLICT ("RestoreID") DO NOTHING;',
            sql_content,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Write modified SQL to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, encoding='utf-8') as tmp_sql:
            tmp_sql.write(sql_content)
            tmp_sql_path = tmp_sql.name

        if restore_op:
            restore_op.RestoreProgress = 80
            restore_op.RestoreMessage = 'Restoring data from backup...'
            restore_op.save()

        # Run the restored SQL
        restore_result = subprocess.run(
            base_cmd + ['-f', tmp_sql_path, '--quiet'],
            env=env, capture_output=True, text=True
        )

        os.unlink(tmp_sql_path)

        if restore_result.returncode != 0:
            logger.error(f"Restoration failed: {restore_result.stderr}")
            if restore_op:
                restore_op.RestoreMessage = f'Data restoration failed: {restore_result.stderr[:200]}'
                restore_op.save()
            return False

        if restore_op:
            restore_op.RestoreProgress = 90
            restore_op.RestoreMessage = 'Finalizing restoration...'
            restore_op.save()

        # Re-enable constraints
        enable_result = subprocess.run(
            base_cmd + ['-c', "SET session_replication_role = 'origin';", '--quiet'],
            env=env, capture_output=True, text=True
        )

        if enable_result.returncode != 0:
            logger.warning(f"Failed to re-enable constraints: {enable_result.stderr}")

        logger.info("Database restoration completed successfully")
        return True

    except Exception as e:
        logger.error(f"Restoration error: {str(e)}")
        if restore_op:
            restore_op.RestoreMessage = f'Restoration error: {str(e)}'
            restore_op.save()
        return False


@login_required
@require_GET
def check_restore_status(request, restore_op_id):
    """Polling endpoint to check restoration status"""
    try:
        restore_op = RestoreOperation.objects.get(RestoreID=restore_op_id)

        return JsonResponse({
            'status': restore_op.RestoreStatus,
            'message': restore_op.RestoreMessage,
            'progress': restore_op.RestoreProgress
        })
    except RestoreOperation.DoesNotExist:
        return JsonResponse({
            'status': 'failed',
            'message': 'Restore operation not found'
        })
