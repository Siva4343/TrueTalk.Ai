from django.urls import path
from .views import SignupView, VerifyOTPView, LoginView, ResendOTPView,GoogleAuthView,SendOTP,VerifyOTP 

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    path("login/", LoginView.as_view(), name="login"),
    path("google/", GoogleAuthView.as_view()),
    path("send-otp/", SendOTP.as_view()),
    path("phone-otp/", VerifyOTP.as_view()),
]

