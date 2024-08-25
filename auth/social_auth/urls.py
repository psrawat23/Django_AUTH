from django.contrib import admin
from django.urls import path, include

urlpatterns = [
        path('accounts/', include('allauth.urls')),

        path('accounts/', include('allauth.socialaccount.urls')),

]