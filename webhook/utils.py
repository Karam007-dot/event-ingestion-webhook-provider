import hmac
import hashlib

def generate_webhook_signature(payload_bytes: bytes, secret_key: str) -> str:
    """
    Generates a cryptographic HMAC SHA256 signature for the webhook payload.
    """
    signature = hmac.new(
        secret_key.encode('utf-8'),
        msg=payload_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    return signature