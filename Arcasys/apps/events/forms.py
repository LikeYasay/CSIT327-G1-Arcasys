from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

DEPARTMENT_CHOICES = [
    ("MO", "Marketing Office (MO)"),
    ("URO", "University Registrar’s Office (URO)"),
    ("OAS", "Office of Admissions & Scholarships (OAS)"),
    ("ETO", "Enrollment Technical Office (ETO)"),
    ("FAO", "Finance & Accounting Office (FAO)"),
    ("SSO", "Student Success Office (SSO)"),
    ("TSG", "Technical Support Group (TSG)"),
    ("GC", "Guidance Center"),
    ("CEA", "College of Engineering & Architecture (CEA)"),
    ("CCS", "College of Computer Studies (CCS)"),
    ("CASE", "College of Arts, Sciences & Education (CASE)"),
    ("CMBA", "College of Management, Business & Accountancy (CMBA)"),
    ("CNAHS", "College of Nursing & Allied Health Sciences (CNAHS)"),
    ("CCJ", "College of Criminal Justice (CCJ)"),
]

class AdminEditEventForm(forms.Form):
    event_title = forms.CharField(label="Event Title", max_length=120, required=True)
    department = forms.ChoiceField(label="Office/Department", choices=DEPARTMENT_CHOICES, required=True)
    event_date = forms.DateField(label="Event Date", required=True, input_formats=["%Y-%m-%d"])
    event_time = forms.TimeField(label="Event Time", required=True, input_formats=["%H:%M"])
    location = forms.CharField(label="Location", max_length=150, required=True)
    description = forms.CharField(label="Event Description", widget=forms.Textarea, required=True)

    # Optional
    tags = forms.CharField(label="Event Tags (comma-separated)", required=False)
    facebook = forms.URLField(label="Facebook Link", required=False)
    tiktok = forms.URLField(label="TikTok Link", required=False)
    youtube = forms.URLField(label="YouTube Link", required=False)
    website = forms.URLField(label="Website Link", required=False)

    # --- Field-level checks ---
    def clean_event_title(self):
        title = self.cleaned_data["event_title"].strip()
        if len(title) < 5:
            raise ValidationError("Title must be at least 5 characters.")
        return title

    def clean_location(self):
        loc = self.cleaned_data["location"].strip()
        if len(loc) < 3:
            raise ValidationError("Location is too short.")
        return loc

    def clean_tags(self):
        raw = self.cleaned_data.get("tags", "").strip()
        if not raw:
            return ""
        tags = [t.strip() for t in raw.split(",") if t.strip()]
        if len(tags) > 10:
            raise ValidationError("Please limit to at most 10 tags.")
        for t in tags:
            if len(t) > 24:
                raise ValidationError("Each tag must be 24 characters or less.")
        return ", ".join(tags)

    # --- Cross-field checks ---
    def clean(self):
        cleaned = super().clean()
        d = cleaned.get("event_date")
        t = cleaned.get("event_time")
        if d and t:
            # compare vs local date/time (prevents events in the past)
            today = timezone.localdate()
            now_time = timezone.localtime().time()
            if d < today or (d == today and t <= now_time):
                raise ValidationError("Event date/time cannot be in the past.")
        return cleaned