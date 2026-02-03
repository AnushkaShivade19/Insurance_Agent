from django.conf import settings
from twilio.rest import Client
from django.core.mail import send_mail

def send_claim_notification(user, claim):
    """
    Sends SMS and Email confirmation to the user.
    """
    # 1. Prepare Message
    msg_body = (
        f"Namaste {user.username}! Your claim #{claim.id} for "
        f"{claim.policy.product.name} (Amount: Rs.{claim.claim_amount}) "
        f"has been received. We are verifying your photo evidence."
    )

    # 2. Send Email
    try:
        send_mail(
            subject=f"Claim Received: #{claim.id}",
            message=msg_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Email Error: {e}")

    # 3. Send SMS (Twilio)
    try:
        # Check if settings exist to avoid crashes during dev
        if hasattr(settings, 'TWILIO_ACCOUNT_SID'):
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            # Use user profile phone or fallback
            user_phone = user.profile.phone_number if hasattr(user, 'profile') and user.profile.phone_number else ''
            
            if user_phone:
                client.messages.create(
                    body=msg_body,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=user_phone
                )
    except Exception as e:
        print(f"Twilio SMS Failed: {e}")