from django.contrib import admin
from .models import Contact, SharedContact

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'user', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['name', 'phone_number', 'email']

@admin.register(SharedContact)
class SharedContactAdmin(admin.ModelAdmin):
    list_display = ['contact_name', 'contact_phone', 'sender', 'receiver', 'shared_at', 'is_accepted']
    list_filter = ['sender', 'receiver', 'shared_at', 'is_accepted']
    search_fields = ['contact_name', 'contact_phone', 'sender__username', 'receiver__username']