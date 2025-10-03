from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role

class CustomUserAdmin(UserAdmin):
    list_display = ('UserEmail', 'UserFullName', 'RoleID', 'isStaff', 'UserCreateAt')
    list_filter = ('RoleID', 'isStaff', 'isActive')
    fieldsets = (
        (None, {'fields': ('UserEmail', 'password')}),
        ('Personal info', {'fields': ('UserFullName', 'RoleID')}),
        ('Permissions', {'fields': ('isActive', 'isStaff', 'isAdmin', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('UserLastLogin', 'UserCreateAt')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('UserEmail', 'UserFullName', 'password1', 'password2', 'RoleID', 'isActive', 'isStaff', 'isAdmin'),
        }),
    )
    search_fields = ('UserEmail', 'UserFullName')
    ordering = ('UserEmail',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(Role)