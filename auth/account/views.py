from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets
from django.contrib.auth import get_user_model
from account.serializers import RegisterSerializer
# from knox.models import AuthToken
from django.contrib.auth import login
from rest_framework import  status
from rest_framework.decorators import api_view
import random
from django.core.cache import cache
from rest_framework.routers import APIRootView
from django.urls import include
import re
from rest_framework.permissions import BasePermission,AllowAny, IsAuthenticated
from django.utils import timezone
import datetime
from account.utility import generate_and_send_otp
from django.core.exceptions import ObjectDoesNotExist
from account.serializers import VerifyAccountSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

# from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()

class ApiRoot(APIRootView):
    def get(self, request, *args, **kwargs):
        urls = include('account.urls')[0].urlpatterns
        response = {}
        for url in urls:
            match = re.search(r'[\w\/\-]+', str(url.pattern))
            if not match:
                continue
            name = match.group()
            response[name] = request.build_absolute_uri(name)
        return Response(response)
    
# @api_view(['GET', 'POST'])
# def redis_test(request, *args, **kwargs):
#     redis_instance = redis.StrictRedis(host = settings.REDIS_HOST,port = settings.REDIS_PORT, db=0 )
#     items = {}
#     count = 0
#     for key in redis_instance.keys("*"):
#         items[key.decode("utf-8")] = redis_instance.get(key)
#         count += 1
#     response = {
#             'count': count,
#             'msg': f"Found {count} items.",
#             'items': items
#     }
#     return Response(response, status=200)



class RegisterView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.check_active()
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)        
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)



class LoginView(APIView):

    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        email_or_phone = request.data.get('email')
        password = request.data.get('password')

        if not email_or_phone or not password:
            return Response("Invalid data,or email/phone password not defined", status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = authenticate(username=email_or_phone,password=password)
            if user is None:
                return Response("Invalid Credentials", status=status.HTTP_400_BAD_REQUEST)
            
            if not user.is_active:
                return Response("User is not active yet", status=status.HTTP_400_BAD_REQUEST)


            refresh = RefreshToken.for_user(user)
            return Response(
                {
                'refresh': str(refresh), 
                 'access': str(refresh.access_token)
                 },
                status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response("Email/Phone do not exists", status=status.HTTP_400_BAD_REQUEST)


class SendOTP(APIView):

    def post(self, request, *args, **kwargs):
        email_or_phone = request.data.get('email')

        if not email_or_phone:
            return Response("Invalid data, email/phone not defined", status=status.HTTP_400_BAD_REQUEST)
        try:
            try:
                user = User.objects.get(email=email_or_phone)
            except ObjectDoesNotExist:
                try:
                    user = User.objects.get(phone=email_or_phone)
                except ObjectDoesNotExist:
                    user = None
                
            if not user:
                return Response(
                    "No User found in db",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Check for max OTP attempts
            if int(user.max_otp_try) == 0 and user.otp_max_out and timezone.now() < user.otp_max_out:
                user.otp_pending = False
                user.save()
                return Response(
                    "Max OTP try reached, try after an hour",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Generate OTP and update user record
            email = user.email
            phone = user.phone
            otp = generate_and_send_otp(phone,email)
            otp_expiry = timezone.now() + datetime.timedelta(minutes=2)
            max_otp_try = int(user.max_otp_try) - 1
            user.otp = otp
            user.otp_expiry = otp_expiry
            user.max_otp_try = max_otp_try
            user.otp_pending = True

            if max_otp_try == 0:
                user.otp_max_out = timezone.now() + datetime.timedelta(hours=1)

            elif max_otp_try == -1:
                user.max_otp_try = 3
            else:
                user.otp_max_out = None
                user.max_otp_try = max_otp_try
            user.save()
            return Response("Successfully generated OTP", status=status.HTTP_200_OK)

        except ObjectDoesNotExist as e:
            return Response(str(e),status=status.HTTP_400_BAD_REQUEST)



class VerifyOTP(APIView):
    def post(self,request,*args,**kwargs):
        try:
            email_or_phone = request.data.get('email')
            otp = request.data.get('otp')

            if not email_or_phone or not otp:
                return Response("Invalid data, email/phone, otp not provided", status=status.HTTP_400_BAD_REQUEST)
            
            try:
                user = User.objects.get(email=email_or_phone)
            except ObjectDoesNotExist:
                try:
                    user = User.objects.get(phone=email_or_phone)
                except ObjectDoesNotExist:
                    user = None

            if not user:
                return Response(
                    "No User found in db",
                    status=status.HTTP_400_BAD_REQUEST,
                )
                
            if not user.otp_pending:
                return Response({
                        'message':'No OTP verification required at this time.',
                        'status': status.HTTP_400_BAD_REQUEST
                    })
            
            if user:
                if user.otp != otp or timezone.now() > user.otp_expiry:  
                    return Response({
                        'message':'otp expired',
                        'status': status.HTTP_400_BAD_REQUEST
                    })

                elif user.otp == otp and timezone.now() < user.otp_expiry:
                    if not user.is_active:
                        user.active = True    

                    user.otp_pending = False   
                    user.otp = None
                    user.otp_expiry = None
                    user.max_otp_try = 3
                    user.otp_max_out = None
                    user.save()
                    
                    return Response({
                        'message':'otp verified',
                        'status': status.HTTP_200_OK
                    })
                else:
                    return Response({
                        'message':'otp not verified',
                        'status': status.HTTP_400_BAD_REQUEST
                    })
                
            return Response({
                'message':'user does not match with db',
                'status': status.HTTP_200_OK
            })
        except Exception as e:
            return Response({
                'message':str(e),
                'status': status.HTTP_400_BAD_REQUEST
            })




# logout api view
# class LogoutView(APIView):
#     permission_classes = (permissions.IsAuthenticated,)

#     def post(self, request, format=None):
#         try:
#             request.user.auth_token.delete()
#             return Response({
#                 'message': 'Logout successfully',
#                 'status': status.HTTP_200_OK,
#             })
#         except Exception as e:
#             return Response({
#                 'message': str(e),
#                 'status': status.HTTP_400_BAD_REQUEST,
#             })