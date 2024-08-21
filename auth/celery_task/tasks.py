from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings




@shared_task(bind=True)
def send_mail(self,email,subject,body):
    try:
        msg = EmailMessage(subject, body, settings.EMAIL_HOST_USER, [email])
        msg.send()
    except Exception as e:
        print(str(e))
        return "SUCCESS"

