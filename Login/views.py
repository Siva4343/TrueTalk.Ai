# login/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import OTP, PendingUser
from .serializers import SignupSerializer, VerifyEmailOTPSerializer, LoginSerializer
import random
from django.core.mail import send_mail
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.db import IntegrityError
from .models import PhoneOTP
from .serializers import PhoneSerializer, VerifyPhoneOTPSerializer
from .utils import send_otp, verify_otp
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests
from .models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken

def generate_otp():
    return str(random.randint(100000, 999999)).zfill(6)

class SignupView(APIView):
    """
    Accepts first_name, last_name, email, password.
    Creates/updates PendingUser and sends OTP to email.
    """
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        email = data["email"].lower()

        # If a real user with this email exists, block signup
        if CustomUser.objects.filter(email=email).exists():
            return Response({"message": "User with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Hash password for safe storage until verification
        password_hashed = make_password(data["password"])

        # Create or update PendingUser
        pending, created = PendingUser.objects.update_or_create(
            email=email,
            defaults={
                "first_name": data["first_name"],
                "last_name": data["last_name"],
                "password_hash": password_hashed,
            }
        )

        # Generate OTP and save
        otp_code = generate_otp()
        OTP.objects.create(email=email, code=otp_code)

        # Send OTP via email
        try:
            send_mail(
                subject="Your OTP Code",
                message=f"Your OTP code is {otp_code}. It expires in 5 minutes.",
                from_email=None,  # uses DEFAULT_FROM_EMAIL if None
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            # In development with console backend this won't error; for SMTP show friendly message
            print("Error sending email:", e)
            return Response({"message": "Failed to send OTP email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"message": "OTP sent to email. Please verify.", "email": email}, status=status.HTTP_200_OK)


class ResendOTPView(APIView):
    """
    Resend OTP for a pending user.
    """
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"message": "Email required."}, status=status.HTTP_400_BAD_REQUEST)
        email = email.lower()
        try:
            if not PendingUser.objects.filter(email=email).exists():
                return Response({"message": "No pending signup for this email."}, status=status.HTTP_400_BAD_REQUEST)

            otp_code = generate_otp()
            OTP.objects.create(email=email, code=otp_code)
            send_mail(
                subject="Your OTP Code - Resend",
                message=f"Your OTP code is {otp_code}. It expires in 5 minutes.",
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )
            return Response({"message": "OTP resent."}, status=status.HTTP_200_OK)
        except Exception as e:
            print("ResendOTP error:", e)
            return Response({"message": "Failed to resend OTP."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyOTPView(APIView):
    """
    Verify the OTP; on success create actual User and delete PendingUser.
    """
    def post(self, request):
        serializer = VerifyEmailOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        email = data["email"].lower()
        otp_input = str(data["otp"]).strip()

        try:
            otp_obj = OTP.objects.filter(email=email).latest("created_at")
        except OTP.DoesNotExist:
            return Response({"message": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        # Check match
        if str(otp_obj.code).strip() != otp_input:
            return Response({"message": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        # Check expiry
        if otp_obj.is_expired():
            return Response({"message": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

        # Find pending user
        try:
            pending = PendingUser.objects.get(email=email)
        except PendingUser.DoesNotExist:
            return Response({"message": "No pending signup found for this email."}, status=status.HTTP_400_BAD_REQUEST)

        # Create actual user
        try:
            user = CustomUser.objects.create_user(
                username=email,
                email=email,
                first_name=pending.first_name,
                last_name=pending.last_name,
                password=pending.password_hash,  # Note: already hashed, so we set it directly
                login_provider="email"
            )
            # Set the hashed password directly since it's already hashed
            user.password = pending.password_hash
            user.save()
        except IntegrityError:
            return Response({"message": "User already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate JWT tokens for immediate login
        refresh = RefreshToken.for_user(user)

        # Clean up: delete pending user and used OTPs (optional)
        pending.delete()
        OTP.objects.filter(email=email).delete()

        return Response({
            "message": "OTP verified. User created.",
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    Login with email & password. Returns JWT tokens on success.
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        email = data["email"].lower()
        password = data["password"]

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"message": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(password):
            return Response({"message": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "message": "Login successful.",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
        }, status=status.HTTP_200_OK)



class GoogleAuthView(APIView):
    def post(self, request):
        token = request.data.get("token")

        try:
            # Verify Google Token
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), settings.GOOGLE_CLIENT_ID
            )

            google_id = idinfo["sub"]
            email = idinfo["email"]
            name = idinfo.get("name", "")
            picture = idinfo.get("picture", "")

            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    "username": email,
                    "first_name": name,
                    "google_id": google_id,
                    "profile_picture": picture,
                    "login_provider": "google"
                }
            )

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.first_name,
                    "profile_picture": user.profile_picture
                }
            }, status=200)

        except Exception:
            return Response({"error": "Invalid Google Token"}, status=400)



class SendOTP(APIView):
    def post(self, request):
        phone = request.data.get("phone")

        status, session_or_msg = send_otp(phone)

        if status == "failed":
            return Response({"message": session_or_msg}, status=400)

        obj, created = PhoneOTP.objects.get_or_create(phone=phone)
        obj.session_id = session_or_msg
        obj.save()

        return Response({"message": "OTP sent successfully"})



class VerifyOTP(APIView):
    def post(self, request):
        phone = request.data.get("phone")
        otp = request.data.get("otp")

        try:
            obj = PhoneOTP.objects.get(phone=phone)
        except PhoneOTP.DoesNotExist:
            return Response({"message": "Phone not found"}, status=400)

        valid = verify_otp(phone, otp, obj.session_id)

        if valid:
            return Response({"message": "OTP Verified Successfully!"})
        else:
            return Response({"message": "Invalid OTP"}, status=400)
