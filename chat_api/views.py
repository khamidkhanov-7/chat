from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import User, Message, ChatRoom, RoomMember, RoomMessage
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer, 
    UserUpdateSerializer, MessageSerializer, MessageCreateSerializer,
    ChatRoomSerializer, RoomMemberSerializer, RoomMessageSerializer,
    RoomMessageCreateSerializer
)


class UserRegistrationView(APIView):
    """Handle user registration"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """Handle user login"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing users"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def update(self, request, *args, **kwargs):
        # Users can only update their own profile
        if request.user.id != int(kwargs.get('pk')):
            return Response(
                {'error': 'You can only update your own profile'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        # Users can only delete their own account
        if request.user.id != int(kwargs.get('pk')):
            return Response(
                {'error': 'You can only delete your own account'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


class MessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing private messages"""
    serializer_class = MessageSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def get_queryset(self):
        # Users can only see messages they sent or received
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        )
    
    @action(detail=False, methods=['get'])
    def conversation(self, request):
        """Get messages between current user and another user"""
        other_user_id = request.query_params.get('user_id')
        if not other_user_id:
            return Response(
                {'error': 'user_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        messages = Message.objects.filter(
            Q(sender=request.user, receiver=other_user) |
            Q(sender=other_user, receiver=request.user)
        ).order_by('created_at')
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        """Mark a message as read"""
        message = get_object_or_404(Message, id=pk, receiver=request.user)
        message.is_read = True
        message.save()
        return Response({'status': 'Message marked as read'})


class ChatRoomViewSet(viewsets.ModelViewSet):
    """ViewSet for managing chat rooms"""
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new chat room and add creator as member"""
        response = super().create(request, *args, **kwargs)
        if response.status_code == status.HTTP_201_CREATED:
            room = ChatRoom.objects.get(id=response.data['id'])
            RoomMember.objects.create(room=room, user=request.user)
        return response
    
    def get_queryset(self):
        # Users can only see rooms they are members of
        return ChatRoom.objects.filter(members=self.request.user)


class RoomMemberViewSet(viewsets.ModelViewSet):
    """ViewSet for managing room members"""
    serializer_class = RoomMemberSerializer
    
    def get_queryset(self):
        # Users can only see memberships for rooms they belong to
        user_rooms = ChatRoom.objects.filter(members=self.request.user)
        return RoomMember.objects.filter(room__in=user_rooms)
    
    def create(self, request, *args, **kwargs):
        """Add a user to a room"""
        room_id = request.data.get('room')
        user_id = request.data.get('user')
        
        # Check if current user is a member of the room
        if not RoomMember.objects.filter(room_id=room_id, user=request.user).exists():
            return Response(
                {'error': 'You must be a member of this room to add others'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Remove a user from a room"""
        membership = self.get_object()
        
        # Users can remove themselves or room members can remove others
        if (membership.user != request.user and 
            not RoomMember.objects.filter(room=membership.room, user=request.user).exists()):
            return Response(
                {'error': 'You can only remove yourself or manage members if you are in the room'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


class RoomMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing room messages"""
    serializer_class = RoomMessageSerializer
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RoomMessageCreateSerializer
        return RoomMessageSerializer
    
    def get_queryset(self):
        # Users can only see messages from rooms they are members of
        user_rooms = ChatRoom.objects.filter(members=self.request.user)
        return RoomMessage.objects.filter(room__in=user_rooms)
    
    @action(detail=False, methods=['get'])
    def by_room(self, request):
        """Get all messages for a specific room"""
        room_id = request.query_params.get('room_id')
        if not room_id:
            return Response(
                {'error': 'room_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user is a member of the room
        if not RoomMember.objects.filter(room_id=room_id, user=request.user).exists():
            return Response(
                {'error': 'You must be a member of this room'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = RoomMessage.objects.filter(room_id=room_id).order_by('created_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)