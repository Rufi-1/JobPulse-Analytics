from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    filter_horizontal = ('skills',)
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = BaseUserAdmin.list_display + ('date_joined',)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'headline', 'desired_role', 'desired_location', 'experience_level', 'is_public', 'completeness')
    list_filter = ('role', 'experience_level', 'open_to_remote', 'is_public')
    search_fields = ('user__username', 'headline', 'desired_role')
    filter_horizontal = ('skills',)
    list_editable = ('role', 'is_public')

    @admin.display(description='Profile completeness')
    def completeness(self, obj):
        return f"{obj.completeness}%"
