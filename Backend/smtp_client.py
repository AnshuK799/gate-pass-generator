
import smtplib
import html

from email.mime.text import MIMEText

from config import (
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USERNAME,
    SMTP_PASSWORD,
    SMTP_FROM
)


def send_visitor_verification_email(to_email, name, otp):

    try:
        msg = MIMEText("", "html")

        msg['From'] = SMTP_FROM
        msg['To'] = to_email
        msg['Subject'] = 'Visitor Verification | DY Patil International University'

        safe_name = html.escape(str(name))
        safe_otp = html.escape(str(otp))

        # Use your publicly hosted university logo URL
        logo_url = "https://www.dypiu.ac.in/assets/images/home/logo.webp"

        email_html = f"""
        <!DOCTYPE html>
        <html>
        <body style="
            margin: 0;
            padding: 15px 10px;
            background-color: #f4f5f7;
            font-family: Arial, Helvetica, sans-serif;
        ">

        <table width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
                <td align="center">

                    <table width="100%" cellpadding="0"
                    cellspacing="0" border="0"
                    style="
                        max-width: 560px;
                        background-color: #ffffff;
                        border: 1px solid #e5e7eb;
                    ">

                        <!-- University Logo -->
                        <tr>
                            <td align="center"
                            style="padding: 15px 15px 10px;">

                                <a href="https://www.dypiu.ac.in/">
                                    <img
                                    src="{logo_url}"
                                    alt="DY Patil International University"
                                    width="220"
                                    style="
                                        display: block;
                                        width: 220px;
                                        max-width: 100%;
                                        height: auto;
                                        border: 0;
                                    ">
                                </a>

                            </td>
                        </tr>

                        <!-- University Brand Colours -->
                        <tr>
                            <td>
                                <table width="100%" cellpadding="0"
                                cellspacing="0" border="0">
                                    <tr>
                                        <td width="45%" height="4"
                                        bgcolor="#168B55"></td>

                                        <td width="10%"
                                        bgcolor="#F29B21"></td>

                                        <td width="45%"
                                        bgcolor="#263B78"></td>
                                    </tr>
                                </table>
                            </td>
                        </tr>

                        <!-- Heading -->
                        <tr>
                            <td align="center"
                            style="padding: 20px 20px 5px;">

                                <h2 style="
                                    margin: 0;
                                    color: #252b46;
                                    font-size: 22px;
                                    font-weight: 700;
                                ">
                                    Visitor Email Verification
                                </h2>

                                <p style="
                                    color: #777777;
                                    font-size: 13px;
                                    margin: 8px 0 0;
                                ">
                                    Welcome to DY Patil International University
                                </p>

                            </td>
                        </tr>

                        <!-- Main Content -->
                        <tr>
                            <td style="
                                padding: 5px 30px 25px;
                            ">

                                <p style="
                                    color: #263238;
                                    font-size: 15px;
                                    margin: 8px 0 12px;
                                ">
                                    Dear <b>{safe_name}</b>,
                                </p>

                                <p style="
                                    color: #555555;
                                    font-size: 14px;
                                    line-height: 1.7;
                                    margin: 10px 0;
                                ">
                                    Thank you for your interest in visiting
                                    DY Patil International University.
                                    We are pleased to assist you with
                                    your campus visit.
                                </p>

                                <p style="
                                    color: #555555;
                                    font-size: 14px;
                                    line-height: 1.7;
                                    margin: 10px 0;
                                ">
                                    To verify your email address and
                                    continue with the visitor verification
                                    process, please use the One-Time
                                    Password (OTP) below.
                                </p>

                                <!-- OTP Box -->
                                <table width="100%" cellpadding="0"
                                cellspacing="0" border="0"
                                style="
                                    margin: 20px 0;
                                    background-color: #f5f7fb;
                                    border: 1px solid #dce2ed;
                                ">
                                    <tr>
                                        <td align="center"
                                        style="padding: 20px 15px;">

                                            <p style="
                                                color: #666666;
                                                font-size: 12px;
                                                font-weight: bold;
                                                letter-spacing: 2px;
                                                margin: 0 0 12px;
                                            ">
                                                YOUR VERIFICATION CODE
                                            </p>

                                            <h1 style="
                                                color: #263B78;
                                                font-size: 34px;
                                                letter-spacing: 10px;
                                                margin: 0;
                                            ">
                                                {safe_otp}
                                            </h1>

                                        </td>
                                    </tr>
                                </table>

                                <!-- Expiry -->
                                <p style="
                                    color: #d97706;
                                    font-size: 13px;
                                    font-weight: bold;
                                    text-align: center;
                                    margin: 12px 0;
                                ">
                                    This OTP is valid for 5 minutes.
                                </p>

                                <p style="
                                    color: #555555;
                                    font-size: 13px;
                                    line-height: 1.7;
                                ">
                                    For security reasons, please do not
                                    share this verification code with
                                    anyone.
                                </p>

                                <p style="
                                    color: #555555;
                                    font-size: 13px;
                                    line-height: 1.7;
                                ">
                                    If you did not request this
                                    verification, you may safely
                                    disregard this email.
                                </p>

                                <!-- Signature -->
                                <p style="
                                    color: #263238;
                                    font-size: 14px;
                                    line-height: 1.7;
                                    margin-top: 20px;
                                ">
                                    Regards,<br>
                                    <b>Visitor Management Team</b><br>
                                    DY Patil International University
                                </p>

                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td align="center"
                            bgcolor="#f5f6f8"
                            style="
                                padding: 18px 15px;
                                border-top: 1px solid #e5e7eb;
                            ">

                                <p style="
                                    color: #263B78;
                                    font-size: 13px;
                                    font-weight: bold;
                                    margin: 0 0 8px;
                                ">
                                    DY Patil International University
                                </p>

                                <a href="https://www.dypiu.ac.in/"
                                style="
                                    color: #168B55;
                                    font-size: 12px;
                                    text-decoration: none;
                                ">
                                    www.dypiu.ac.in
                                </a>

                                <p style="
                                    color: #999999;
                                    font-size: 11px;
                                    margin: 12px 0 0;
                                ">
                                    Automated Visitor Verification Email
                                </p>

                                <p style="
                                    color: #aaaaaa;
                                    font-size: 10px;
                                    margin-bottom: 0;
                                ">
                                    Think | Thrive | Transform
                                </p>

                            </td>
                        </tr>

                    </table>

                </td>
            </tr>
        </table>

        </body>
        </html>
        """

        msg.set_payload(email_html)

        # Send Email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Visitor verification email sent to {to_email}")

    except Exception as e:
        print(f"Failed to send visitor verification email: {e}")

