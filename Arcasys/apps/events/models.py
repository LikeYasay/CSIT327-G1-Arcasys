import uuid
from django.db import models
from django.utils import timezone     

# ==============================
# EVENT MODEL
# ==============================

class Event(models.Model):
    EventID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='EventID'
    )
    EventTitle = models.CharField(
        max_length=255, 
        db_column='EventTitle'
    )
    EventDescription = models.TextField(
        db_column='EventDescription'
    )
    EventDate = models.DateField(
        db_column='EventDate'
    )
    EventTime = models.TimeField(
        db_column='EventTime'
    )
    EventLocation = models.CharField(
        max_length=255, 
        db_column='EventLocation'
    )
    EventCreatedAt = models.DateTimeField(
        default=timezone.now,
        db_column='EventCreatedAt'
    )
    EventUpdatedAt = models.DateTimeField(
        default=timezone.now,
        db_column='EventUpdatedAt'
    )

    class Meta:
        db_table = 'Event'

    def __str__(self):
        return self.EventTitle

class Tag(models.Model):
    TagID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='TagID'
    )
    TagName = models.CharField(
        max_length=100, 
        unique=True, 
        db_column='TagName'
    )

    class Meta:
        db_table = 'Tag'

    def __str__(self):
        return self.TagName

class Department(models.Model):
    DepartmentID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='DepartmentID'
    )
    DepartmentName = models.CharField(
        max_length=255, 
        unique=True, 
        db_column='DepartmentName'
    )

    class Meta:
        db_table = 'Department'

    def __str__(self):
        return self.DepartmentName

# ------------------------------
# JUNCTION MODELS
# ------------------------------

class EventTag(models.Model):
    EventTagID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='EventTagID'
    )
    # EventID (FK) - Links to Event
    EventID = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        db_column='EventID'
    )
    # TagID (FK) - Links to Tag
    TagID = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        db_column='TagID'
    )

    EventTagAssignedAt = models.DateTimeField(
        default=timezone.now, 
        db_column='EventTagAssignedAt'
    )

    class Meta:
        db_table = 'EventTag'
        unique_together = ('EventID', 'TagID')

    def __str__(self):
        return f"Tag {self.TagID} on Event {self.EventID}"

class EventDepartment(models.Model):
    EventDepartmentID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='EventDepartmentID'
    )
    # EventID (FK)
    EventID = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        db_column='EventID'
    )
    # DepartmentID (FK)
    DepartmentID = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        db_column='DepartmentID'
    )
    EventDepartmentAssignedAt = models.DateTimeField(
        default=timezone.now,
        db_column='EventDepartmentAssignedAt'
    )

    class Meta:
        db_table = 'EventDepartment'
        unique_together = ('EventID', 'DepartmentID')

    def __str__(self):
        return f"Dept {self.DepartmentID} for Event {self.EventID}"

class EventLink(models.Model):
    EventLinkID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='EventLinkID'
    )
    # EventID (FK)
    EventID = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        db_column='EventID'
    )
    EventLinkName = models.CharField(
        max_length=255, 
        db_column='EventLinkName'
    )
    EventLinkURL = models.URLField(
        max_length=2000, 
        db_column='EventLinkURL'
    )

    class Meta:
        db_table = 'EventLink'

    def __str__(self):
        return f"{self.EventLinkName} for Event {self.EventID}"