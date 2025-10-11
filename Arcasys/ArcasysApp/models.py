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
        extra_fields.setdefault('isUserAdmin', True)
        extra_fields.setdefault('isUserActive', True)
        extra_fields.setdefault('isUserStaff', False)
        
        # Get or create admin role - CHANGE TO 'Admin'
        admin_role, created = Role.objects.get_or_create(
            RoleName='Admin',  # ✅ Changed from 'Archive Administrator' to 'Admin'
            defaults={'RoleDescription': 'Full system administrator with user management privileges'}
        )
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
    UserPasswordHash = models.CharField(
        max_length=128,
        blank=True,
        db_column='UserPasswordHash'
    )
    UserCreatedAt = models.DateTimeField(  # ✅ Changed from UserCreateAt to UserCreatedAt
        default=timezone.now,
        db_column='UserCreatedAt'
    )
    UserLastLogin = models.DateTimeField(
        null=True, 
        blank=True,
        db_column='UserLastLogin'
    )
    
    # ACCOUNT APPROVAL SYSTEM - UPDATED NAMES
    isUserActive = models.BooleanField(  # ✅ Changed from isActive to isUserActive
        default=False,
        db_column='isUserActive'
    )
    UserApprovedBy = models.ForeignKey(  # ✅ Changed from approved_by to UserApprovedBy
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        db_column='UserApprovedBy',
        related_name='approved_users'
    )
    UserApprovedAt = models.DateTimeField(  # ✅ Changed from approved_at to UserApprovedAt
        null=True, 
        blank=True,
        db_column='UserApprovedAt'
    )
    
    isUserAdmin = models.BooleanField(  # ✅ Changed from isAdmin to isUserAdmin
        default=False,
        db_column='isUserAdmin'
    )
    isUserStaff = models.BooleanField(  # ✅ Changed from isStaff to isUserStaff
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
    
    # Property mappings - UPDATED to match new field names
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
        return self.isUserAdmin  # ✅ Updated to isUserAdmin
    
    @is_superuser.setter
    def is_superuser(self, value):
        self.isUserAdmin = value  # ✅ Updated to isUserAdmin
    
    @property
    def is_staff(self):
        return self.isUserStaff  # ✅ Updated to isUserStaff
    
    @is_staff.setter
    def is_staff(self, value):
        self.isUserStaff = value  # ✅ Updated to isUserStaff
    
    @property
    def is_active(self):
        return self.isUserActive  # ✅ Updated to isUserActive
    
    @is_active.setter
    def is_active(self, value):
        self.isUserActive = value  # ✅ Updated to isUserActive