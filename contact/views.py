from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Contact, SharedContact
from .serializers import ContactSerializer, SharedContactSerializer, ShareContactSerializer, UserSerializer

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SharedContactViewSet(viewsets.ModelViewSet):
    serializer_class = SharedContactSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SharedContact.objects.filter(receiver=self.request.user)

    @action(detail=False, methods=['post'])
    def share_contact(self, request):
        serializer = ShareContactSerializer(data=request.data)
        if serializer.is_valid():
            receiver = get_object_or_404(User, id=serializer.validated_data['receiver_id'])
            
            # Check if user is trying to share with themselves
            if receiver == request.user:
                return Response(
                    {'error': 'You cannot share a contact with yourself.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            shared_contact = SharedContact.objects.create(
                sender=request.user,
                receiver=receiver,
                contact_name=serializer.validated_data['contact_name'],
                contact_phone=serializer.validated_data['contact_phone'],
                contact_email=serializer.validated_data.get('contact_email', '')
            )
            
            return Response(
                SharedContactSerializer(shared_contact).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def accept_contact(self, request, pk=None):
        shared_contact = get_object_or_404(SharedContact, pk=pk, receiver=request.user)
        
        # Check if contact already exists
        existing_contact = Contact.objects.filter(
            user=request.user,
            phone_number=shared_contact.contact_phone
        ).first()
        
        if existing_contact:
            shared_contact.is_accepted = True
            shared_contact.save()
            return Response(
                {'status': 'Contact already exists in your contacts'},
                status=status.HTTP_200_OK
            )
        
        # Add to user's contacts
        Contact.objects.create(
            user=request.user,
            name=shared_contact.contact_name,
            phone_number=shared_contact.contact_phone,
            email=shared_contact.contact_email
        )
        
        shared_contact.is_accepted = True
        shared_contact.save()
        
        return Response({'status': 'Contact added to your contacts'})

    @action(detail=True, methods=['post'])
    def reject_contact(self, request, pk=None):
        shared_contact = get_object_or_404(SharedContact, pk=pk, receiver=request.user)
        shared_contact.delete()
        
        return Response({'status': 'Contact share rejected'})

class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Return all users except the current user
        return User.objects.exclude(id=self.request.user.id)