import json
import time
import qrcode
import base64
from io import BytesIO

def generate_qr_code(email, name, address, purpose):
    """Generate a QR code containing visitor information."""
    visitor_info = {
        "email": email,
        "name": name,
        "address": address,
        "purpose": purpose
    }
    visitor_info_json = json.dumps(visitor_info)
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(visitor_info_json)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert image to base64 string
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    return img_str
  
