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
    RoleDescription = models.TextField(
        blank=True,
        db_column='RoleDescription'
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
        
        # Handle Role assignment properly
        role = extra_fields.pop('RoleID', None)
        user = self.model(UserEmail=email, **extra_fields)
        if role:
            user.RoleID = role
        
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, UserEmail, password=None, **extra_fields):
        extra_fields.setdefault('isStaff', True)
        extra_fields.setdefault('isAdmin', True)
        
        # Get or create admin role - pass the instance, not the UUID
        admin_role, created = Role.objects.get_or_create(
            RoleName='Admin',
            defaults={'RoleDescription': 'System administrator with full access'}
        )
        extra_fields['RoleID'] = admin_role  # Pass the Role instance
        
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
    UserPasswordHash = models.CharField(
        max_length=128,
        blank=True,
        db_column='UserPasswordHash'
    )
    UserCreateAt = models.DateTimeField(
        default=timezone.now,
        db_column='UserCreateAt'
    )
    UserLastLogin = models.DateTimeField(
        null=True, 
        blank=True,
        db_column='UserLastLogin'
    )
    isActive = models.BooleanField(
        default=True,
        db_column='isActive'
    )
    isAdmin = models.BooleanField(
        default=False,
        db_column='isAdmin'
    )
    isStaff = models.BooleanField(
        default=False,
        db_column='isStaff'
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'UserEmail'
    REQUIRED_FIELDS = ['UserFullName']
    EMAIL_FIELD = 'UserEmail'  # Fix for password reset
    
    class Meta:
        db_table = 'User'
    
    def __str__(self):
        return f"{self.UserFullName} ({self.UserEmail})"
    
    # Property mappings to connect Django's expected fields to your custom fields
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
        return self.isAdmin
    
    @is_superuser.setter
    def is_superuser(self, value):
        self.isAdmin = value
    
    @property
    def is_staff(self):
        return self.isStaff
    
    @is_staff.setter
    def is_staff(self, value):
        self.isStaff = value
    
    @property
    def is_active(self):
        return self.isActive
    
    @is_active.setter
    def is_active(self, value):
        self.isActive = value
    
    def save(self, *args, **kwargs):
        if not self.RoleID_id:
            # Assign default role if not set
            default_role, created = Role.objects.get_or_create(
                RoleName='Viewer',
                defaults={'RoleDescription': 'Basic user with view-only access'}
            )
            self.RoleID = default_role
        super().save(*args, **kwargs)