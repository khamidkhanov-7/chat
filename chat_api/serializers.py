from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, Message, ChatRoom, RoomMember, RoomMessage


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True, 
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include username and password')
        
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user data"""
    class Meta:
        model = User
        fields = ['username', 'email']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for private messages"""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'receiver', 'sender_username', 
            'receiver_username', 'content', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at']


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating private messages"""
    class Meta:
        model = Message
        fields = ['receiver', 'content']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class ChatRoomSerializer(serializers.ModelSerializer):
    """Serializer for chat rooms"""
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ['id', 'name', 'created_at', 'member_count']
        read_only_fields = ['id', 'created_at']
    
    def get_member_count(self, obj):
        return obj.members.count()


class RoomMemberSerializer(serializers.ModelSerializer):
    """Serializer for room members"""
    username = serializers.CharField(source='user.username', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    
    class Meta:
        model = RoomMember
        fields = ['id', 'room', 'user', 'username', 'room_name', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class RoomMessageSerializer(serializers.ModelSerializer):
    """Serializer for room messages"""
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)
    
    class Meta:
        model = RoomMessage
        fields = [
            'id', 'room', 'sender', 'sender_username', 
            'room_name', 'content', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at']


class RoomMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating room messages"""
    class Meta:
        model = RoomMessage
        fields = ['room', 'content']
    
    def create(self, validated_data):
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate_room(self, value):
        user = self.context['request'].user
        if not RoomMember.objects.filter(room=value, user=user).exists():
            raise serializers.ValidationError(
                "You must be a member of this room to send messages"
            )
        return value