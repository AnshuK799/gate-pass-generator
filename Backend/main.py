import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from smtp_client import send_visitor_verification_email
from db_helpers import insert_into_visitors
from otp_helpers import generate_otp, check_otp
from generate_qr import generate_qr_code
from generate_pass_pdf import generate_visitor_pass_pdf
from config import OTP_DELIVERY, SMTP_CONFIGURED

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/generate_otp")
async def generate_otp_endpoint(request: Request):
    data = await request.json()
    email = data.get("email")
    if not email:
        return JSONResponse(status_code=400, content={"message": "Email is required."})

    otp = generate_otp(email)
    if otp is None:
        return JSONResponse(status_code=500, content={"message": "Failed to generate OTP."})

    use_smtp = OTP_DELIVERY == "smtp" or (OTP_DELIVERY == "auto" and SMTP_CONFIGURED)
    if use_smtp:
        if not send_visitor_verification_email(email, "Visitor", otp):
            return JSONResponse(status_code=502, content={"message": "Could not send the verification email. Please try again later."})
    else:
        # Local development fallback when SMTP has not been configured.
        print(f"Visitor OTP for {email}: {otp}")

    response = {"message": "OTP generated and sent successfully."}
    if not use_smtp:
        response["development_otp"] = otp
    return JSONResponse(status_code=200, content=response)

@app.post("/submit_visitor")
async def submit_visitor(request: Request):
    data = await request.json()
    name = data.get("name")
    address = data.get("address")
    email = data.get("email")
    purpose = data.get("purpose")
    otp = data.get("otp")

    if not all([name, address, email, purpose, otp]):
        return JSONResponse(status_code=400, content={"message": "All fields are required."})

    if not check_otp(email, otp):
        return JSONResponse(status_code=400, content={"message": "Invalid or expired OTP."})    

    # Insert visitor data into the database
    response = insert_into_visitors(name, address, email, purpose)
    if not response:
        return JSONResponse(status_code=500, content={"message": "Failed to insert visitor data into the database."})   
    else:
        qr_code = generate_qr_code(email, name, address, purpose)
        pass_pdf = generate_visitor_pass_pdf(name, address, email, purpose)
        return JSONResponse(status_code=200, content={"message": "Visitor data inserted successfully.", "qr_code": qr_code, "visitor_pass_pdf": pass_pdf})
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
