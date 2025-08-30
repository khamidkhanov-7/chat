from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    UserRegistrationView, UserLoginView, UserViewSet, 
    MessageViewSet, ChatRoomViewSet, RoomMemberViewSet, RoomMessageViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'rooms', ChatRoomViewSet)
router.register(r'room-members', RoomMemberViewSet, basename='roommember')
router.register(r'room-messages', RoomMessageViewSet, basename='roommessage')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', UserRegistrationView.as_view(), name='register'),
    path('auth/login/', UserLoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API endpoints
    path('', include(router.urls)),
]