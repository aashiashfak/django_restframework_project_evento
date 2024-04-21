import qrcode
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

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