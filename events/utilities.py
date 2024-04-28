import qrcode
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from .models import Ticket,Payment
import razorpay
from django.conf import settings

def generate_qr_code(data):
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    # Generate QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert QR code image to BytesIO
    img_io = BytesIO()
    qr_img.save(img_io, format='PNG')
    img_io.seek(0)

    # Convert BytesIO to InMemoryUploadedFile
    return InMemoryUploadedFile(
        img_io, None, f"ticket_qr_code.png", 'image/png', img_io.tell(), None
    )


def initiate_razorpay_payment(ticket_id):

    try:
    # Retrieve ticket details
        ticket = Ticket.objects.get(pk=ticket_id)

        # Initialize Razorpay client with your Razorpay API key and secret
        client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

        # Create order data
        order_data = {
            "amount": int(ticket.ticket_price) * 100, 
            "currency": "INR", 
            "payment_capture": "1"
        }

        # Create order
        razorpay_order = client.order.create(data=order_data)

        # Extract the order ID from the Razorpay response
        razorpay_order_id = razorpay_order['id']
        # razorpay_order_status = razorpay_order['status']

        # Create a new Payment instance
        payment = Payment.objects.create(
            ticket=ticket,
            order_id=razorpay_order_id,
            amount=ticket.ticket_price,
            status='pending'  # Set initial status as pending
        )

        payment_data = {
                "order_id": razorpay_order_id,
                "amount": order_data["amount"],
                "currency": order_data["currency"],
                "status": payment.status  
            }
        return payment_data
    except Exception as e:
        print(f"Error during payment initiation: {str(e)}")

        error_message = str(e)
        return error_message
    

def verify_razorpay_signature(signature, payload):
    """
    Verifies the signature of a Razorpay webhook request.

    Args:
        signature: The signature received in the webhook request.
        payload: The payload received in the webhook request.

    Returns:
        True if the signature is valid, False otherwise.
    """

    # Create a Razorpay client instance
    client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

    try:
        # Verify the signature using Razorpay's utility function
        is_verified = client.utility.verify_payment_signature(signature, payload)
        return is_verified
    except Exception as e:
        print(f"Error verifying Razorpay signature: {e}")
        return False
