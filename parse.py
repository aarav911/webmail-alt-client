from webmail import *
import webmail
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup


test = connect()
mailboxes = get_mailboxes(test)
current_mailbox = mailboxes[4]

print("You chose: " + current_mailbox)

test.select(current_mailbox)
status, data = test.search(None, "ALL")
print("Status: " + status)
ids = data[0].split()
latest = ids[-1]
status, msg = test.fetch(latest, "(RFC822)")
raw_email = msg[0][1]


# Recommended: Parse with modern policy immediately
msg = BytesParser(policy=policy.default).parsebytes(raw_email)   
# body = msg.get_content()

text_body =None
html_body = None
attachments = []

for part in msg.walk():
    content_type = part.get_content_type()
    disposition = str(part.get("Content-Disposition", ""))

    if part.get_content_maintype() == "multipart":
        continue

    if content_type == "text/plain" and "attachment" not in disposition:
        text_body = part.get_content() #returns the decoded string
    elif content_type == "text/html" and "attachment" not in disposition:
        html_body = part.get_content()
    
    elif "attachment" in disposition:
        filename = part.get_filename()
        if filename:
            payload = part.get_content() #returns byte automatically decoded
            attachments.append({"filename": filename, "data": payload})

print(text_body)
# print(html_body)
print(attachments)



soup = BeautifulSoup(html_body, 'html.parser')
print(soup.text)








# print("This is msg variable: \n\n")
# # print(msg)



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

# for part in msg.walk():
    # print(part)

# print(msg.is_multipart())
# print(msg.get_content_type)
# for part in msg.walk():
#     print(part.get_content_type)


# for k,v in msg.items():
#     print(k + " : "+ v)


# for i, part in enumerate(msg.walk()):
#     print("="*50)
#     print(i)
#     print("TYPE:", part.get_content_type())
#     print("MAINTYPE:", part.get_content_maintype())
#     print("SUBTYPE:", part.get_content_subtype())
#     print("DISPOSITION:", part.get_content_disposition())

# for i, part in enumerate(msg.walk()):
#     print("="*50)
#     print(i)
#     print("TYPE:", part.get_content_type())

#     payload = part.get_payload(decode=True)

#     if payload:
#         print(payload[:200])

close(test)

