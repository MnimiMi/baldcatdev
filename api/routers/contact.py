import os
import resend
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/contact", tags=["contact"])

_TO_EMAIL = os.getenv("CONTACT_TO_EMAIL", "")
_FROM_EMAIL = os.getenv("CONTACT_FROM_EMAIL", "contact@tell.guru")


class ContactRequest(BaseModel):
    firstName: str = ""
    lastName: str = ""
    email: str = ""
    subject: str = ""
    message: str = ""
    website: str = ""  # honeypot — боты заполняют, люди нет


@router.post("")
def send_contact(req: ContactRequest):
    if req.website:
        return {"success": True}

    api_key = os.getenv("RESEND_API_KEY", "")
    if not api_key or not _TO_EMAIL:
        return {"error": "Email service not configured"}

    resend.api_key = api_key

    name = f"{req.firstName} {req.lastName}".strip() or req.email
    subject = req.subject.strip() or "Contact Form"

    resend.Emails.send({
        "from": _FROM_EMAIL,
        "to": [_TO_EMAIL],
        "reply_to": req.email or None,
        "subject": f"[tell.guru] {subject}",
        "html": (
            f"<p><strong>From:</strong> {name}"
            + (f" &lt;{req.email}&gt;" if req.email else "")
            + f"</p>"
            f"<p><strong>Subject:</strong> {subject}</p>"
            f"<hr/>"
            f"<p>{req.message.replace(chr(10), '<br/>')}</p>"
        ),
    })
    return {"success": True}
