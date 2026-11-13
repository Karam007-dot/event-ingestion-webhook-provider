import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler

SECRET_KEY = 'your-secure-shared-secret-key'

class WebhookReceiverHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h3>Mock Webhook Receiver is active and listening for POST requests!</h3>")

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        signature_header = self.headers.get('X-Webhook-Signature', '')
        
        expected_signature = hmac.new(
            SECRET_KEY.encode('utf-8'),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        provided_signature = signature_header.replace('sha256=', '')
        is_valid = hmac.compare_digest(expected_signature, provided_signature)
        
        print(f"\n[Mock Receiver] Received Webhook Event!")
        print(f" -> Event ID Header: {self.headers.get('X-Webhook-Event-Id')}")
        print(f" -> Signature Valid: {is_valid}")
        print(f" -> Payload Body: {body.decode('utf-8')}")
        
        if is_valid:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'Webhook received and verified successfully!')
        else:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'Invalid HMAC signature!')

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', 8080), WebhookReceiverHandler)
    print("Mock Webhook Receiver listening on http://127.0.0.1:8080 ...")
    server.serve_forever()