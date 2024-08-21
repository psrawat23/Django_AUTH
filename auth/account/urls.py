from django.urls import path,include
from account.views import *
from rest_framework import routers
# from knox.views import LogoutView



router = routers.DefaultRouter()
router.register(r'', RegisterView, basename='task')


urlpatterns = [ 

    # list the api URLS 
    path('',ApiRoot.as_view()),
    path('user-register/',include(router.urls)),
    path('send_otp/',SendOTP.as_view()),
    path('user-login/',LoginView.as_view()),
    path('verify_otp/',VerifyOTP.as_view())
]  