"""Create a one-page visitor pass PDF with a vector QR code."""

import base64
import json
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

import qrcode


PAGE_WIDTH = 595
PAGE_HEIGHT = 842


def _pdf_text(value):
    """Encode a text value as a safe WinAnsi PDF string."""
    encoded = str(value).encode("cp1252", errors="replace")
    escaped = bytearray()
    for byte in encoded:
        if byte in (ord("("), ord(")"), ord("\\")):
            escaped.extend(b"\\" + bytes((byte,)))
        elif byte < 32 or byte > 126:
            escaped.extend(f"\\{byte:03o}".encode("ascii"))
        else:
            escaped.append(byte)
    return b"(" + bytes(escaped) + b")"


def _text(x, y, size, value, font="F1", color="0.12 0.17 0.29"):
    return (
        f"BT /{font} {size} Tf {color} rg {x} {y} Td ".encode("ascii")
        + _pdf_text(value)
        + b" Tj ET\n"
    )


def _wrap(value, max_chars):
    words = str(value).split()
    lines = []
    current = ""
    for word in words:
        while len(word) > max_chars:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:max_chars])
            word = word[max_chars:]
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _qr_matrix(email, name, address, purpose):
    visitor_info = {
        "email": email,
        "name": name,
        "address": address,
        "purpose": purpose,
    }
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=4,
    )
    qr.add_data(json.dumps(visitor_info))
    qr.make(fit=True)
    return qr.get_matrix()


def generate_visitor_pass_pdf(name, address, email, purpose):
    """Return a base64 encoded, branded PDF visitor pass."""
    commands = bytearray()

    # DYPIU color band and heading.
    commands.extend(b"0.15 0.23 0.47 rg 0 730 595 112 re f\n")
    commands.extend(b"0.09 0.55 0.33 rg 0 724 595 6 re f\n")
    commands.extend(b"0.95 0.61 0.13 rg 0 719 595 5 re f\n")
    commands.extend(_text(48, 797, 11, "DY PATIL INTERNATIONAL UNIVERSITY", "F2", "1 1 1"))
    commands.extend(_text(48, 766, 23, "VISITOR PASS", "F2", "1 1 1"))
    commands.extend(_text(48, 746, 9, "VISITOR MANAGEMENT SYSTEM", "F1", "0.86 0.90 0.97"))

    # Visitor details.
    commands.extend(_text(48, 684, 10, "VISITOR DETAILS", "F2", "0.09 0.55 0.33"))
    commands.extend(b"0.86 0.89 0.93 RG 48 675 m 547 675 l S\n")

    y = 649
    fields = [
        ("VISITOR NAME", name, 42),
        ("EMAIL ADDRESS", email, 48),
        ("ADDRESS", address, 52),
        ("PURPOSE OF VISIT", purpose, 48),
    ]
    for label, value, max_chars in fields:
        commands.extend(_text(48, y, 8, label, "F2", "0.39 0.44 0.53"))
        y -= 17
        lines = _wrap(value, max_chars)
        for line in lines:
            commands.extend(_text(48, y, 10, line, "F1", "0.12 0.17 0.29"))
            y -= 14
        y -= 10

    issued = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST")
    commands.extend(_text(48, max(290, y - 4), 8, "PASS ISSUED", "F2", "0.39 0.44 0.53"))
    commands.extend(_text(48, max(274, y - 20), 10, issued))

    # Draw QR cells as PDF rectangles so the pass stays self-contained.
    matrix = _qr_matrix(email, name, address, purpose)
    matrix_size = len(matrix)
    qr_size = 156
    cell = qr_size / matrix_size
    qr_x, qr_y = 389, 390
    commands.extend(b"1 1 1 rg 378 379 178 178 re f\n")
    commands.extend(b"0.86 0.89 0.93 RG 378 379 178 178 re S\n")
    commands.extend(b"0 0 0 rg\n")
    for row_index, row in enumerate(matrix):
        column = 0
        while column < matrix_size:
            if not row[column]:
                column += 1
                continue
            start = column
            while column < matrix_size and row[column]:
                column += 1
            width = (column - start) * cell
            x = qr_x + start * cell
            y_cell = qr_y + (matrix_size - row_index - 1) * cell
            commands.extend(f"{x:.3f} {y_cell:.3f} {width:.3f} {cell:.3f} re f\n".encode("ascii"))
    commands.extend(_text(410, 363, 8, "SCAN AT CAMPUS ENTRANCE", "F2", "0.15 0.23 0.47"))

    # Arrival note and campus address.
    commands.extend(b"0.94 0.97 0.95 rg 48 174 499 61 re f\n")
    commands.extend(b"0.09 0.55 0.33 rg 48 174 3 61 re f\n")
    commands.extend(_text(64, 211, 10, "PLEASE KEEP THIS PASS READY ON ARRIVAL", "F2", "0.15 0.23 0.47"))
    commands.extend(_text(64, 191, 9, "Present the QR code to the university security team at the entrance."))
    commands.extend(_text(48, 103, 9, "DY Patil International University", "F2", "0.15 0.23 0.47"))
    commands.extend(_text(48, 87, 8, "Sector 29, Akurdi, Pune, Maharashtra 411044"))
    commands.extend(_text(48, 52, 8, "Think  |  Thrive  |  Transform", "F2", "0.09 0.55 0.33"))
    commands.extend(_text(431, 52, 8, "VISITOR HUB  ·  DYPIU", "F2", "0.39 0.44 0.53"))

    stream = bytes(commands)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
    ]

    pdf = BytesIO()
    pdf.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id, body in enumerate(objects, start=1):
        offsets.append(pdf.tell())
        pdf.write(f"{object_id} 0 obj\n".encode("ascii"))
        pdf.write(body)
        pdf.write(b"\nendobj\n")
    xref_offset = pdf.tell()
    pdf.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return base64.b64encode(pdf.getvalue()).decode("ascii")
