from django.contrib import admin

# Register your models here.
from .models import ChatRoom, Message, MessageReaction, UserStatus, ArchivedChat, ChatBackup
admin.site.register(ChatRoom)
admin.site.register(Message)
admin.site.register(MessageReaction)
admin.site.register(UserStatus)
admin.site.register(ArchivedChat)
admin.site.register(ChatBackup)