
import requests
import json
from config import TERMII_API_KEY, TERMII_BASE_URL, TERMII_SENDER_ID

class SMSService:
    """Handles sending SMS alerts via Termii."""

    def __init__(self):
        self.api_key = TERMII_API_KEY
        self.base_url = TERMII_BASE_URL
        self.sender_id = TERMII_SENDER_ID

    def is_configured(self):
        return bool(self.api_key)

    def send_alert(self, to_number, message):
        """
        Send an SMS alert.
        
        Args:
            to_number (str): The recipient's phone number (international format preferred, e.g., 234...).
            message (str): The message content.
        
        Returns:
            dict: Response from Termii API or error dict.
        """
        if not self.is_configured():
            return {"error": "SMS Service not configured (Missing API Key)."}

        url = f"{self.base_url}/sms/send"
        
        # Termii specific payload
        payload = {
            "to": to_number,
            "from": self.sender_id,
            "sms": message,
            "type": "plain",
            "channel": "generic", # or 'dnd' depending on use case users
            "api_key": self.api_key,
        }
        
        headers = {
            'Content-Type': 'application/json',
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            response_data = response.json()
            
            if response.status_code == 200:
                return {"success": True, "data": response_data}
            else:
                 return {"success": False, "error": response_data.get("message", "Unknown error")}
                 
        except Exception as e:
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Test
    sms = SMSService()
    if sms.is_configured():
        print("SMS Service Configured.")
    else:
        print("SMS Service NOT Configured.")
