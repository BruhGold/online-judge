from django.contrib import admin
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils.timezone import localtime

class SessionAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'user', 'expire_date']

    def user(self, obj):
        data = obj.get_decoded()
        user_id = data.get('_auth_user_id')
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        except:
            return 'Unknown'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True
