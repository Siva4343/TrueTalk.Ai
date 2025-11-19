from django.contrib import admin

# Register your models here.
from . models import OTP, PendingUser, PhoneOTP, CustomUser
admin.site.register(OTP)
admin.site.register(PendingUser)
admin.site.register(PhoneOTP)
admin.site.register(CustomUser)