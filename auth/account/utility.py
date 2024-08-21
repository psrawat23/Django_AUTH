import requests
from django.conf import settings
from django.template.loader import render_to_string
import random
from django.core.cache import cache
from celery_task import tasks
from django.utils import timezone
import datetime

def send_otp(mobile, otp):
    """
    Send OTP via SMS.
    """
    url = f"https://2factor.in/API/V1/{settings.SMS_API_KEY}/SMS/{mobile}/{otp}/Your OTP is"
    payload = ""
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    response = requests.get(url, data=payload, headers=headers)
    print(response.content)
    return bool(response.ok)


def generate_otp():
    otp = random.randint(1000, 9999)   
    return otp



def generate_and_send_otp(phone=None,email=None):
        
        # If otp is cached return it, do not send mail
        if cache.get(email):
             return cache.get(email)
        
        # IF otp is not cached generate and do not create new for 30 seconds
        otp = generate_otp()
        cache.set(email,otp,30)
        
        if email:    
            subject = "OTP Verification"
            body  = render_to_string(
                        "email/mail_otp_verification.html",
                        {
                            "otp_code": otp,
                            "otp_validity": timezone.now() + datetime.timedelta(minutes=2)
                        },
            )
            task = tasks.send_mail.delay(email,subject,body)
            print(task)
        return otp
