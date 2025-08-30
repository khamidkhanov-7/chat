from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Message, ChatRoom, RoomMember, RoomMessage


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['username', 'email']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'content', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['content', 'sender__username', 'receiver__username']
    readonly_fields = ['created_at']


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'member_count']
    search_fields = ['name']
    readonly_fields = ['created_at']
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(RoomMember)
class RoomMemberAdmin(admin.ModelAdmin):
    list_display = ['room', 'user', 'joined_at']
    list_filter = ['joined_at']
    search_fields = ['room__name', 'user__username']
    readonly_fields = ['joined_at']


@admin.register(RoomMessage)
class RoomMessageAdmin(admin.ModelAdmin):
    list_display = ['room', 'sender', 'content', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'room__name', 'sender__username']
    readonly_fields = ['created_at']