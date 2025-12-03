from django.urls import path
from .views import (
    BusinessProfileDetail,
    UserSearchView,
    SendVerificationEmail,
    VerifyEmailCode,
    RegisterAPIView,
)

urlpatterns = [
    path('profile/', BusinessProfileDetail.as_view(), name='business-profile'),
    path('search/', UserSearchView.as_view(), name='user-search'),
    path('send-verification-email/', SendVerificationEmail.as_view(), name='send-verification'),
    path('verify-email-code/', VerifyEmailCode.as_view(), name='verify-email'),
    path('register/', RegisterAPIView.as_view(), name='register'),
]
