from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .models import BusinessProfile
from .serializers import BusinessProfileSerializer, UserWithProfileSerializer
from django.core.mail import send_mail
from django.conf import settings
import random
import string

# STORE VERIFICATION CODES IN MEMORY (NO SESSION → NO CSRF)
verification_storage = {}  # {email: code}


class SendVerificationEmail(APIView):
    permission_classes = []  # Public

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        # Generate code
        code = "".join(random.choices(string.digits, k=6))

        # Save (no CSRF required)
        verification_storage[email] = code

        # Send mail
        send_mail(
            "Email Verification Code",
            f"Your verification code is: {code}",
            settings.EMAIL_HOST_USER,
            [email],
        )

        return Response({"message": "Verification code sent"})

class RegisterAPIView(APIView):
    permission_classes = []  # Public endpoint

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")

        # VALIDATION
        if not username:
            return Response({"username": ["This field is required"]}, status=400)
        if not email:
            return Response({"email": ["This field is required"]}, status=400)
        if not password:
            return Response({"password": ["This field is required"]}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({"username": ["Username already exists"]}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"email": ["Email already exists"]}, status=400)

        # CREATE USER SAFELY (IMPORTANT)
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        user.set_password(password)  # Hashes password correctly
        user.save()

        # CREATE PROFILE
        BusinessProfile.objects.get_or_create(user=user)

        return Response({"message": "User registered successfully"}, status=201)


class VerifyEmailCode(APIView):
    permission_classes = []  # Public

    def post(self, request):
        code = request.data.get("code")
        email = request.data.get("email")

        if not code or not email:
            return Response({"error": "Code and email required"}, status=400)

        stored_code = verification_storage.get(email)

        if stored_code != code:
            return Response({"error": "Invalid verification code"}, status=400)

        # Verify user
        try:
            user = User.objects.get(email=email)
            profile = user.business_profile
            profile.is_verified = True
            profile.save()

            # Remove code
            verification_storage.pop(email, None)

            return Response({"message": "Email verified successfully"})
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)


class BusinessProfileDetail(generics.RetrieveUpdateAPIView):
    serializer_class = BusinessProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.business_profile


class UserSearchView(generics.ListAPIView):
    serializer_class = UserWithProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get("q", "")
        return User.objects.filter(
            username__icontains=query
        ) | User.objects.filter(
            email__icontains=query
        ) | User.objects.filter(
            business_profile__business_name__icontains=query
        )
