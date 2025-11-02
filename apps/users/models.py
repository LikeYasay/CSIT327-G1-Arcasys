import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class Role(models.Model):
    RoleID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='RoleID'
    )
    RoleName = models.CharField(
        max_length=50,
        unique=True,
        db_column='RoleName'
    )

    class Meta:
        db_table = 'Role'

    def __str__(self):
        return self.RoleName


class UserManager(BaseUserManager):
    def create_user(self, UserEmail, password=None, **extra_fields):
        if not UserEmail:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(UserEmail)

        if 'RoleID' not in extra_fields:
            staff_role, created = Role.objects.get_or_create(RoleName='Staff')
            extra_fields['RoleID'] = staff_role

        user = self.model(UserEmail=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, UserEmail, password=None, **extra_fields):
        extra_fields.setdefault('isUserAdmin', True)
        extra_fields.setdefault('isUserActive', True)
        extra_fields.setdefault('isUserStaff', False)

        admin_role, created = Role.objects.get_or_create(RoleName='Admin')
        extra_fields['RoleID'] = admin_role

        return self.create_user(UserEmail, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    UserID = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column='UserID'
    )
    RoleID = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        db_column='RoleID'
    )
    UserFullName = models.CharField(
        max_length=255,
        db_column='UserFullName'
    )
    UserEmail = models.EmailField(
        unique=True,
        db_column='UserEmail'
    )

    # ✅ REQUIRED: Django AbstractBaseUser needs this exact field name
    password = models.CharField(
        max_length=128,
        db_column='UserPasswordHash'  # Maps to your existing database column
    )

    UserCreatedAt = models.DateTimeField(
        default=timezone.now,
        db_column='UserCreatedAt'
    )
    UserLastLogin = models.DateTimeField(
        null=True,
        blank=True,
        db_column='UserLastLogin'
    )

    isUserActive = models.BooleanField(
        default=False,
        db_column='isUserActive'
    )
    isUserAdmin = models.BooleanField(
        default=False,
        db_column='isUserAdmin'
    )
    isUserStaff = models.BooleanField(
        default=False,
        db_column='isUserStaff'
    )

    UserApprovedBy = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='UserApprovedBy',
        related_name='approved_users'
    )
    UserApprovedAt = models.DateTimeField(
        null=True,
        blank=True,
        db_column='UserApprovedAt'
    )

    isUserAdmin = models.BooleanField(
        default=False,
        db_column='isUserAdmin'
    )
    isUserStaff = models.BooleanField(
        default=False,
        db_column='isUserStaff'
    )

    objects = UserManager()

    USERNAME_FIELD = 'UserEmail'
    REQUIRED_FIELDS = ['UserFullName']
    EMAIL_FIELD = 'UserEmail'

    class Meta:
        db_table = 'User'

    def __str__(self):
        return f"{self.UserFullName} ({self.UserEmail})"

    # KEEP YOUR PROPERTY MAPPINGS
    @property
    def password(self):
        return self.UserPasswordHash

    @password.setter
    def password(self, value):
        self.UserPasswordHash = value

    @property
    def last_login(self):
        return self.UserLastLogin

    @last_login.setter
    def last_login(self, value):
        self.UserLastLogin = value

    @property
    def is_superuser(self):
        return self.isUserAdmin

    @is_superuser.setter
    def is_superuser(self, value):
        self.isUserAdmin = value

    @property
    def is_staff(self):
        return self.isUserStaff

    @is_staff.setter
    def is_staff(self, value):
        self.isUserStaff = value

    @property
    def is_active(self):
        return self.isUserActive

    @is_active.setter
    def is_active(self, value):
        self.isUserActive = value
