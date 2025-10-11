from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role

class CustomUserAdmin(UserAdmin):
    # Update list_display with new field names
    list_display = ('UserEmail', 'UserFullName', 'RoleID', 'isUserStaff', 'UserCreatedAt', 'isUserActive')
    
    # Update list_filter with new field names  
    list_filter = ('RoleID', 'isUserStaff', 'isUserActive', 'UserCreatedAt')
    
    # Update fieldsets with new field names
    fieldsets = (
        (None, {'fields': ('UserEmail', 'password')}),
        ('Personal info', {'fields': ('UserFullName', 'RoleID')}),
        ('Permissions', {'fields': ('isUserActive', 'isUserStaff', 'isUserAdmin')}),
        ('Important dates', {'fields': ('UserLastLogin', 'UserCreatedAt', 'UserApprovedAt')}),
        ('Approval Info', {'fields': ('UserApprovedBy',)}),
    )
    
    # Update add_fieldsets with new field names
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('UserEmail', 'UserFullName', 'password1', 'password2', 'RoleID', 'isUserStaff', 'isUserActive'),
        }),
    )
    
    search_fields = ('UserEmail', 'UserFullName')
    ordering = ('UserCreatedAt',)
    filter_horizontal = ()

# Register your models
admin.site.register(User, CustomUserAdmin)
admin.site.register(Role)