import hmac
import hashlib
import base64

def generate_license(user_id, secret_key="YOUR_SECRET_KEY"):
    message = f"{user_id}-{timezone.now().strftime('%Y-%m-%d')}"
    signature = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256).digest()
    license_key = base64.urlsafe_b64encode(signature).decode('utf-8')[:16]
    return license_key

# مثال استفاده
user_id = "test_user"
license = generate_license(user_id)
print(f"License Key: {license}")