from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser"""
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username


class Message(models.Model):
    """Model for private messages between two users"""
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"


class ChatRoom(models.Model):
    """Model for group chat rooms"""
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(
        User, 
        through='RoomMember', 
        related_name='chat_rooms'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class RoomMember(models.Model):
    """Model for tracking room membership"""
    room = models.ForeignKey(
        ChatRoom, 
        on_delete=models.CASCADE, 
        related_name='room_members'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='memberships'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('room', 'user')
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.username} in {self.room.name}"


class RoomMessage(models.Model):
    """Model for messages in group chat rooms"""
    room = models.ForeignKey(
        ChatRoom, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='room_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message in {self.room.name} by {self.sender.username}"