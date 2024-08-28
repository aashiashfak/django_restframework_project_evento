import qrcode
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import TicketType,Payment
import razorpay
from django.conf import settings

def generate_qr_code(payment):
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_data = f"Ticket ID: {payment.order_id}\nEvent: {payment.ticket_type.event.event_name}"
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Generate QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert QR code image to BytesIO
    img_io = BytesIO()
    qr_img.save(img_io, format='PNG')
    img_io.seek(0)

    # Convert BytesIO to InMemoryUploadedFile
    return InMemoryUploadedFile(
        img_io, None, f"ticket_qr_code{payment.order_id}.png", 'image/png', img_io.tell(), None
    )


def initiate_razorpay_payment(ticket_id, ticket_count):
    try:
        # Retrieve ticket details
        ticket = TicketType.objects.get(pk=ticket_id)

        # Initialize Razorpay client with your Razorpay API key and secret
        client = razorpay.Client(auth=(settings.RAZORPAY_API_KEYS, settings.RAZORPAY_API_SECRET_KEY))
        print('apikey',settings.RAZORPAY_API_KEYS,'secret:', settings.RAZORPAY_API_SECRET_KEY)
        print('client',client)


        # Create order data
        order_data = {
            "amount": int(ticket.price* ticket_count) * 100,  # Amount should be in the smallest unit (e.g., paise)
            "currency": "INR",
            "payment_capture": "1",
        }

        # Create order
        razorpay_order = client.order.create(data=order_data)

        # Extract the order ID from the Razorpay response
        razorpay_order_id = razorpay_order['id']

        # Prepare payment data
        payment_data = {
            "order_id": razorpay_order_id,
            "amount": order_data["amount"],
            "currency": order_data["currency"],
        }

        return payment_data
    except Exception as e:
        # Log the error and return a structured response indicating failure
        print(f"Error during payment initiation: {str(e)}")
        return {"error": str(e)}
    

import hmac
import hashlib

def verify_razorpay_signature(received_signature, payload, secret_key):
    generated_signature = hmac.new(
        key=secret_key.encode('utf-8'),
        msg=payload.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(received_signature, generated_signature)