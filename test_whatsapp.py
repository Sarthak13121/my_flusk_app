from twilio.rest import Client
import os

# ----------------------------------------------------------------------
# WARNING: HARD-CODING TOKENS IS FOR IMMEDIATE TESTING ONLY. 
# THIS IS NOT SECURE FOR PRODUCTION USE.
# ----------------------------------------------------------------------

# Your hard-coded Account SID and Auth Token from your last message
ACCOUNT_SID = 'AC5db571bb528a49a6d02928f61d3f0a88'
AUTH_TOKEN = '4104b5b668211b37af85475120bda421'

# The Twilio Sandbox number from your last message (FROM)
WHATSAPP_SENDER = 'whatsapp:+14155238886'

# The number you want to send the message TO (must be verified/joined the sandbox)
# Replace this with the verified number from image_142a22.png or your own phone number
WHATSAPP_RECIPIENT = 'whatsapp:+918849693716'

# Initialize the Twilio Client
try:
    client = Client(ACCOUNT_SID, AUTH_TOKEN)
except Exception as e:
    print(f"CLIENT INITIALIZATION FAILED: {e}")
    print("Ensure you have set the correct TWILIO_ACCOUNT_SID and AUTH_TOKEN.")
    exit()

print(f"Attempting to send message from {WHATSAPP_SENDER} to {WHATSAPP_RECIPIENT}...")

try:
    # Attempt to send a simple text message
    message = client.messages.create(
        from_=WHATSAPP_SENDER,
        body='Testing Twilio connection from Flask troubleshooting script. If you receive this, the 401 error is fixed!',
        to=WHATSAPP_RECIPIENT
    )
    
    print("\n--- MESSAGE STATUS ---")
    print(f"Message successfully created with SID: {message.sid}")
    print(f"Status: {message.status}")
    print("----------------------\n")

except Exception as e:
    # This block catches the 401 error or other API failure codes
    print("\n!!! TWILIO API ERROR !!!")
    print(f"Error Code: {e.code if hasattr(e, 'code') else 'Unknown'}")
    print(f"Details: {e}")
    print("\nThis likely means the AUTH_TOKEN is wrong or your Sandbox is not active.")


# ----------------------------------------------------------------------
# EXECUTION STEPS:
# 1. Ensure your phone number (+918849693716) has sent the "join <sandbox name>" message to the Twilio number.
# 2. Run this script in your VENV: python test_whatsapp.py
# ----------------------------------------------------------------------