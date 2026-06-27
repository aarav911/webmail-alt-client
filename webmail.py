
import imaplib
from email import message_from_bytes
from email import policy
from email.parser import BytesParser

EMAIL = "24b2177@iitb.ac.in"
TOKEN = "2d0b787242b92507cb7756ac3fe0960d"


class Email:

    def __init__(
        self,
        sender="",
        recipients=None,
        subject="",
        date="",
        text_body=None,
        html_body=None,
        attachments=None
    ):
        self.sender = sender
        self.recipients = recipients or []
        self.subject = subject
        self.date = date

        self.text_body = text_body
        self.html_body = html_body

        self.attachments = attachments or []

    def __str__(self):

        text_preview = ""

        if self.text_body:
            text_preview = self.text_body.strip()
            text_preview = text_preview.replace("\n", " ")
            text_preview = text_preview[:2004]

            if len(self.text_body) > 200:
                text_preview += "..."

        attachment_names = [
            a["filename"]
            for a in self.attachments
        ]

        return (
            "\n"
            "============================================================\n"
            f"Subject      : {self.subject}\n"
            f"From         : {self.sender}\n"
            f"To           : {', '.join(self.recipients)}\n"
            f"Date         : {self.date}\n"
            f"Text Body    : {'Yes' if self.text_body else 'No'}\n"
            f"HTML Body    : {'Yes' if self.html_body else 'No'}\n"
            f"Attachments  : {len(self.attachments)}\n"
            f"Files        : {attachment_names}\n"
            "\n"
            "Body Preview:\n"
            "------------------------------------------------------------\n"
            f"{text_preview}\n"
            "============================================================"
        )

#function to make the connection and return the mail obj
def connect():

    try:
        print("Connecting...")

        mail = imaplib.IMAP4_SSL(
            host="imap.iitb.ac.in",
            port=993
        )

        print("Connected.")
        print("Logging in...")

        status, data = mail.login(EMAIL, TOKEN)

        print("Login status:", status)
        print("Response:", data)

        

        return mail
    
        # mail.select("INBOX")
        # status, data = mail.search(None, "ALL")
        # ids = data[0].split()
        # # print(ids)
        # latest = ids[-2]


        # status, msg = mail.fetch(latest, "(RFC822)") #thats the standard we assume webmail uses. 
        # # print(msg[0][1]) #raw email

        # raw_email = msg[0][1]
        # msg = message_from_bytes(raw_email)
        # # print(msg["Subject"])
        # # print(msg["From"])
        # # print(msg["Date"])
        # # print(msg["Body"]) Does not exist

        # # print(type(msg))
        # # print(dir(msg)) #to get the methods
        # # print(vars(msg)) # to get the values stored

        # for part in msg.walk():
        #     print(part.get_content_type())
            

        # # print(msg[0][1].decode(errors="replace")[:])

    except Exception as e:
        print(type(e).__name__)
        print(e)

#to close the connection
def close(mail):
    mail.logout()

#function to printout the different mailboxes available
def get_mailboxes(mail):
    status, mailboxes = mail.list()
    mb = []
    for mailbox in mailboxes:
        (mb.append(mailbox.decode().split()[-1]))
    return mb
       
#function to ask the user for the mailbox they want to select
def select_mailbox(mailboxes):
    print("Select Mailbox: ")
    for i, t in enumerate(mailboxes):
        print("Enter " + (str(i))+ " for " + t)
    choice = input()
    return mailboxes[int(choice)]

#function to get the 10 latest emails in the current mailbox and output a list, of subjects, and from
def get_n_emails(current_mailbox, mail, n):
    mail.select(current_mailbox)
    status, data = mail.search(None, "ALL")
    print("Status: " + status)
    ids = data[0].split()
    latest = ids[-1:-(n+1):-1]
    emails = []
    for i, l in enumerate(latest):
        print("Getting email: " + str(i+1))
        status, msg = mail.fetch(l, "(RFC822)")
        raw_email = msg[0][1]
        msg = BytesParser(policy=policy.default).parsebytes(raw_email)   
        email= parse_and_build_msg(msg)
        emails.append(email)
    return emails

'''
msg(this is how the msg data is like)
│
├── Headers
│   ├── Subject
│   ├── From
│   ├── Date
│   └── ...
│
└── MIME Tree
    ├── text/plain
    ├── text/html
    └── attachments

so the algorithm becomes: 
1. extract headers
2. walk MIME tree
    1. if text/plain: do that
    2. if "whatever": do "whatever"
3. Build the email object
4. return the email object.
'''
#to parse and build the msg more properly into an email object, instance of an Email class. 
def parse_and_build_msg(msg):

    sender = msg.get("From", "")
    recipients = msg.get_all("To", [])
    subject = msg.get("Subject", "")
    date = msg.get("Date", "")

    text_body = None
    html_body = None
    attachments = []

    for part in msg.walk():

        content_type = part.get_content_type()
        disposition = str(part.get("Content-Disposition", ""))

        if part.get_content_maintype() == "multipart":
            continue

        if (
            content_type == "text/plain"
            and "attachment" not in disposition
        ):
            text_body = part.get_content()

        elif (
            content_type == "text/html"
            and "attachment" not in disposition
        ):
            html_body = part.get_content()

        elif "attachment" in disposition:

            filename = part.get_filename()

            if filename:
                attachments.append(
                    {
                        "filename": filename,
                        "data": part.get_content()
                    }
                )

    return Email(
        sender=sender,
        recipients=recipients,
        subject=subject,
        date=date,
        text_body=text_body,
        html_body=html_body,
        attachments=attachments
    )

#function to print emails
def print_emails(emails):
    for i,e in enumerate(emails):
        print("#####################################")
        print("Email No: "+ str(i+1))
        print(e)
        print("#####################################")
        print("\n\n\n")




def main():

    my_mail = connect()
    mailboxes = get_mailboxes(my_mail)
    print(mailboxes)
    current_mailbox = select_mailbox(mailboxes)
    print("You chose: " + current_mailbox)
    print("How many emails would you like to get? ")
    n = input()
    emails = get_n_emails(current_mailbox, my_mail, int(n))
    print_emails(emails)
    close(my_mail)


main()


'''
TODO Features:
1. should get notification, of new webmails, each time i start my computer. if any. 
2. ml classification, to predict the importance of that email. 
3. standalone python gui, to be run...

'''





