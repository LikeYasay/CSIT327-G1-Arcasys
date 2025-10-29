from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role

class CustomUserAdmin(UserAdmin):
    list_display = ('UserEmail', 'UserFullName', 'RoleID', 'isUserStaff', 'UserCreatedAt', 'isUserActive')
    list_filter = ('RoleID', 'isUserStaff', 'isUserActive', 'UserCreatedAt')
    fieldsets = (
        (None, {'fields': ('UserEmail', 'password')}),
        ('Personal info', {'fields': ('UserFullName', 'RoleID')}),
        ('Permissions', {'fields': ('isUserActive', 'isUserStaff', 'isUserAdmin')}),
        ('Important dates', {'fields': ('UserLastLogin', 'UserCreatedAt', 'UserApprovedAt')}),
        ('Approval Info', {'fields': ('UserApprovedBy',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('UserEmail', 'UserFullName', 'password1', 'password2', 'RoleID', 'isUserStaff', 'isUserActive'),
        }),
    )
    search_fields = ('UserEmail', 'UserFullName')
    ordering = ('UserCreatedAt',)
    filter_horizontal = ()

admin.site.register(User, CustomUserAdmin)
admin.site.register(Role)