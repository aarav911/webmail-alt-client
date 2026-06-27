import os
import json
from email import message_from_bytes
from email import policy
from email.parser import BytesParser
import imaplib
from email import policy
from email.parser import BytesParser, HeaderParser
import threading
from concurrent.futures import ThreadPoolExecutor
from email.header import decode_header



CONFIG_FILE = "webmail_config.json"


def clean_from_field(raw_from):
    """Simplifies the 'From' column to show a clean sender name."""
    full_name = clean_header(raw_from)
    if "<" in full_name:
        name_part = full_name.split("<")[0].strip()
        if name_part:
            return name_part.strip('"')
    return full_name

def clean_header(raw_header):
    """Decodes RFC 2047 headers (like =?utf-8?q?...) into clean text."""
    if not raw_header:
        return ""
    try:
        from email.header import decode_header
        decoded_parts = decode_header(raw_header)
        header_text = ""
        for bytes_or_str, encoding in decoded_parts:
            if isinstance(bytes_or_str, bytes):
                header_text += bytes_or_str.decode(encoding or "utf-8", errors="replace")
            else:
                header_text += bytes_or_str
        return header_text.strip().strip('"').strip("'")
    except Exception:
        return str(raw_header)

class Email:
    def __init__(self, msg_id, sender="", recipients=None, subject="", date="", 
                 text_body=None, html_body=None, attachments=None, loaded=False):
        self.msg_id = msg_id  # Keep track of server side ID for late-binding loads
        self.sender = sender
        self.recipients = recipients or []
        self.subject = subject
        self.date = date
        self.text_body = text_body
        self.html_body = html_body
        self.attachments = attachments or []
        self.loaded = loaded


class MailBackend:
    def __init__(self):
        self.host = "imap.iitb.ac.in"
        self.port = 993
        self.mail = None
        self.email_address = ""
        self.token = ""
        self.load_credentials()

    def load_credentials(self):
        """Loads client connection profiles without local shell variables."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.email_address = data.get("email", "24b2177@iitb.ac.in")
                    self.token = data.get("sso_token", "")
                    return
            except Exception as e:
                print(f"Failed parsing local config: {e}")
        
        self.email_address = "24b2177@iitb.ac.in"
        self.token = ""

    def save_credentials(self, email, token):
        """Saves current properties profile safely down into JSON structure."""
        self.email_address = email
        self.token = token
        with open(CONFIG_FILE, "w") as f:
            json.dump({"email": email, "sso_token": token}, f, indent=4)

    def connect(self):
        if not self.token:
            return False, "Missing Token"
        try:
            if self.mail:
                try: self.mail.logout()
                except: pass
            self.mail = imaplib.IMAP4_SSL(host=self.host, port=self.port)
            status, data = self.mail.login(self.email_address, self.token)
            if status == "OK":
                return True, "Success"
            return False, str(data)
        except Exception as e:
            return False, str(e)

    def get_mailboxes(self):
        if not self.mail: return []
        try:
            status, mailboxes = self.mail.list()
            if status != "OK": return []
            cleaned_boxes = []
            for box in mailboxes:
                parts = box.decode().split()
                box_name = parts[-1].strip('"')
                cleaned_boxes.append(box_name)
            return cleaned_boxes
        except:
            return []

    def fetch_latest_headers(self, mailbox_name, limit=25):
        """Optimization: Only downloads minimal header metadata needed for layout mapping."""
        if not self.mail: return []
        try:
            self.mail.select(mailbox_name, readonly=True)
            status, data = self.mail.search(None, "ALL")
            if status != "OK" or not data[0]: return []

            message_ids = data[0].split()
            target_ids = message_ids[-1:-(limit + 1):-1]
            
            emails = []
            header_parser = HeaderParser()

            for msg_id in target_ids:
                # OPTIMIZATION: Request ONLY fundamental tracking values (saves bandwidth/time)
                status, msg_data = self.mail.fetch(msg_id, "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE)])")
                if status != "OK": continue
                
                raw_headers = msg_data[0][1].decode(errors='replace')
                parsed_hdrs = header_parser.parsestr(raw_headers)

                raw_from = parsed_hdrs.get("From", "Unknown")
                raw_subject = parsed_hdrs.get("Subject", "(No Subject)")

                emails.append(Email(
                    msg_id=msg_id,
                    sender=clean_from_field(raw_from),
                    subject=clean_header(raw_subject),
                    date=parsed_hdrs.get("Date", ""),
                    loaded=False  # Postpone downloading the body text until clicked
                ))
            return emails
        except Exception as e:
            print(f"Header fetch error: {e}")
            return []

    def load_full_body(self, mailbox_name, email_obj):
        """Late-binding engine loading specific targeted message text parts dynamically."""
        if not self.mail or email_obj.loaded: return email_obj
        try:
            self.mail.select(mailbox_name, readonly=True)
            status, msg_data = self.mail.fetch(email_obj.msg_id, "(RFC822)")
            if status != "OK": return email_obj
            
            raw_bytes = msg_data[0][1]
            msg = BytesParser(policy=policy.default).parsebytes(raw_bytes)
            
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))
                if part.get_content_maintype() == "multipart": continue

                if content_type == "text/plain" and "attachment" not in disposition:
                    email_obj.text_body = part.get_content()
                elif content_type == "text/html" and "attachment" not in disposition:
                    email_obj.html_body = part.get_content()
                elif "attachment" in disposition:
                    filename = part.get_filename()
                    if filename:
                        email_obj.attachments.append({
                            "filename": filename,
                            "data": part.get_content()
                        })
            email_obj.loaded = True
            return email_obj
        except Exception as e:
            print(f"Full body fetch failed: {e}")
            return email_obj


