from flask import request, make_response
from functools import wraps
import mysql.connector
import re
import os
import uuid

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from icecream import ic
ic.configureOutput(prefix=f'***** | ', includeContext=True)

UNSPLASH_ACCESS_KEY = 'YOUR_KEY_HERE'
ADMIN_ROLE_PK = "16fd2706-8baf-433b-82eb-8c7fada847da"
CUSTOMER_ROLE_PK = "c56a4180-65aa-42ec-a945-5fd21dec0538"
PARTNER_ROLE_PK = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
RESTAURANT_ROLE_PK = "9f8c8d22-5a67-4b6c-89d7-58f8b8cb4e15"


# form to get data from input fields
# args to get data from the url
# values to get data from the url and from the form

class CustomException(Exception):
    def __init__(self, message, code):
        super().__init__(message)  # Initialize the base class with the message
        self.message = message  # Store additional information (e.g., error code)
        self.code = code  # Store additional information (e.g., error code)

def raise_custom_exception(error, status_code):
    raise CustomException(error, status_code)


##############################
def db():
    db = mysql.connector.connect(
        host="mysql",      # Replace with your MySQL server's address or docker service name "mysql"
        user="root",  # Replace with your MySQL username
        password="password",  # Replace with your MySQL password
        database="company"   # Replace with your MySQL database name
    )
    cursor = db.cursor(dictionary=True)
    return db, cursor


##############################
def no_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    return no_cache_view


##############################

def allow_origin(origin="*"):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Call the wrapped function
            response = make_response(f(*args, **kwargs))
            # Add Access-Control-Allow-Origin header to the response
            response.headers["Access-Control-Allow-Origin"] = origin
            # Optionally allow other methods and headers for full CORS support
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            return response
        return decorated_function
    return decorator


##############################
USER_NAME_MIN = 2
USER_NAME_MAX = 20
USER_NAME_REGEX = f"^.{{{USER_NAME_MIN},{USER_NAME_MAX}}}$"
def validate_user_name():
    error = f"name {USER_NAME_MIN} to {USER_NAME_MAX} characters"
    user_name = request.form.get("user_name", "").strip()
    if not re.match(USER_NAME_REGEX, user_name): raise_custom_exception(error, 400)
    return user_name

##############################
USER_LAST_NAME_MIN = 2
USER_LAST_NAME_MAX = 20
USER_LAST_NAME_REGEX = f"^.{{{USER_LAST_NAME_MIN},{USER_LAST_NAME_MAX}}}$"
def validate_user_last_name():
    error = f"last name {USER_LAST_NAME_MIN} to {USER_LAST_NAME_MAX} characters"
    user_last_name = request.form.get("user_last_name", "").strip() # None
    if not re.match(USER_LAST_NAME_REGEX, user_last_name): raise_custom_exception(error, 400)
    return user_last_name

##############################
REGEX_EMAIL = "^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"
def validate_user_email():
    error = "email invalid"
    user_email = request.form.get("user_email", "").strip()
    if not re.match(REGEX_EMAIL, user_email): raise_custom_exception(error, 400)
    return user_email

##############################
USER_PASSWORD_MIN = 8
USER_PASSWORD_MAX = 50
REGEX_USER_PASSWORD = f"^.{{{USER_PASSWORD_MIN},{USER_PASSWORD_MAX}}}$"
def validate_user_password():
    error = f"password {USER_PASSWORD_MIN} to {USER_PASSWORD_MAX} characters"
    user_password = request.form.get("user_password", "").strip()
    if not re.match(REGEX_USER_PASSWORD, user_password): raise_custom_exception(error, 400)
    return user_password
##############################
USER_USER_CONFIRM_NEWPASSWORD_MIN = 8
USER_USER_CONFIRM_NEWPASSWORD_PASSWORD_MAX = 50
REGEX_USER_CONFIRM_NEWPASSWORD__PASSWORD = f"^.{{{USER_USER_CONFIRM_NEWPASSWORD_MIN},{USER_USER_CONFIRM_NEWPASSWORD_PASSWORD_MAX}}}$"
def validate_user_confirm_new_password():
    error = f"password {USER_PASSWORD_MIN} to {USER_PASSWORD_MAX} characters"
    user_confirm_new_password = request.form.get("user_confirm_new_password", "").strip()
    if not re.match(REGEX_USER_CONFIRM_NEWPASSWORD__PASSWORD, user_confirm_new_password): raise_custom_exception(error, 400)
    return user_confirm_new_password





##############################
USER_PASSWORD_MIN = 8
USER_PASSWORD_MAX = 50
REGEX_USER_PASSWORD = f"^.{{{USER_PASSWORD_MIN},{USER_PASSWORD_MAX}}}$"
def validate_new_user_password(new_password):
    error = f"password {USER_PASSWORD_MIN} to {USER_PASSWORD_MAX} characters"
    user_password = request.form.get("user_password", "").strip()
    if not re.match(REGEX_USER_PASSWORD, new_password): raise_custom_exception(error, 400)
    return new_password

##############################
ITEM_TITLE_MIN = 2
ITEM_TITLE_MAX = 50
ITEM_TITLE_REGEX = f"^.{{{ITEM_TITLE_MIN},{ITEM_TITLE_MAX}}}$"
def validate_item_title():
    error = f"Title must be between {ITEM_TITLE_MIN} and {ITEM_TITLE_MAX} characters"
    item_title = request.form.get("item_title", "").strip()
    if not re.match(ITEM_TITLE_REGEX, item_title): raise_custom_exception(error, 400)
    return item_title

ITEM_DESCRIPTION_MIN = 5
ITEM_DESCRIPTION_MAX = 500
ITEM_DESCRIPTION_REGEX = f"^.{{{ITEM_DESCRIPTION_MIN},{ITEM_DESCRIPTION_MAX}}}$"
def validate_item_description():
    error = f"Description must be between {ITEM_DESCRIPTION_MIN} and {ITEM_DESCRIPTION_MAX} characters"
    item_description = request.form.get("item_description", "").strip()
    if not re.match(ITEM_DESCRIPTION_REGEX, item_description): raise_custom_exception(error, 400)
    return item_description

def validate_item_price():
    error = "Invalid price"
    try:
        item_price = float(request.form.get("item_price", "").strip())
        if item_price <= 0:
            raise_custom_exception(error, 400)
        return item_price
    except ValueError:
        raise_custom_exception(error, 400)






##############################
REGEX_UUID4 = "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
def validate_uuid4(uuid4 = ""):
    error = f"invalid uuid4"
    if not uuid4:
        uuid4 = request.values.get("uuid4", "").strip()
    if not re.match(REGEX_UUID4, uuid4): raise_custom_exception(error, 400)
    return uuid4

##############################
UPLOAD_ITEM_FOLDER = './static/images'
ALLOWED_ITEM_FILE_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
REGEX_ITEM_IMAGE = r'^.*\.(jpg|jpeg|png|gif)$'

def validate_item_image():
    if 'item_file' not in request.files: raise_custom_exception("item_file missing", 400)
    file = request.files.get("item_file", "")
    if file.filename == "": raise_custom_exception("item_file name invalid", 400)

    if file:
        ic(file.filename)
        file_extension = os.path.splitext(file.filename)[1][1:]
        ic(file_extension)
        if file_extension not in ALLOWED_ITEM_FILE_EXTENSIONS: raise_custom_exception("item_file invalid extension", 400)
        filename = str(uuid.uuid4())+"." + file_extension
        return file, filename 


##############################
def send_verify_email(to_email, user_verification_key):
    try:
        # Create a gmail fullflaskdemomail
        # Enable (turn on) 2 step verification/factor in the google account manager
        # Visit: https://myaccount.google.com/apppasswords


        # Email and password of the sender's Gmail account
        sender_email = "wrathzeek@gmail.com"
        password = "qxea cqda veji leia"  # If 2FA is on, use an App Password instead

        # Receiver email address
        receiver_email = "wrathzeek@gmail.com"
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "My company name"
        message["To"] = receiver_email
        message["Subject"] = "Please verify your account"

        # Body of the email
        body = f"""To verify your account, please <a href="http://127.0.0.1/verify/{user_verification_key}">click here</a>"""
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")

        return "email sent"
       
    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass


##############################
def send_order_email():
    try:
        # Create a gmail fullflaskdemomail
        # Enable (turn on) 2 step verification/factor in the google account manager
        # Visit: https://myaccount.google.com/apppasswords


        # Email and password of the sender's Gmail account
        sender_email = "webdevjenner@gmail.com"
        password = "crrn qrfi uusx cduj"  # If 2FA is on, use an App Password instead

        # Receiver email address
        receiver_email = "magnusmadsen2000@hotmail.com"
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "My company name"
        message["To"] = receiver_email
        message["Subject"] = "WWWolt order details"

        # Body of the email
        body = f"""Your order details: 1x burger, 1x fries, 1x coke"""
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")
        
        return "email sent"
       
    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass

##############################
def send_block_email(to_email, type_of_block):
    try:
        # Create a gmail fullflaskdemomail
        # Enable (turn on) 2 step verification/factor in the google account manager
        # Visit: https://myaccount.google.com/apppasswords


        # Email and password of the sender's Gmail account
        sender_email = "wrathzeek@gmail.com"
        password = "qxea cqda veji leia"  # If 2FA is on, use an App Password instead

        # Receiver email address
        receiver_email = "wrathzeek@gmail.com"
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "Wolt"
        message["To"] = receiver_email
        message["Subject"] = "Account update"

        # Body of the email
        body = f"""<p>Your {item_or_user} have been {type_of_block} by an admin!</p>"""
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")

        return "email sent"
       
    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass

##############################
def send_partner_email(to_email, verification_key):
    try:
        # Create a gmail fullflaskdemomail
        # Enable (turn on) 2 step verification/factor in the google account manager
        # Visit: https://myaccount.google.com/apppasswords


        # Email and password of the sender's Gmail account
        sender_email = "webdevjenner@gmail.com"
        password = "crrn qrfi uusx cduj"  # If 2FA is on, use an App Password instead

        # Receiver email address
        receiver_email = "webdevjenner@gmail.com"
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "Wolt"
        message["To"] = receiver_email
        message["Subject"] = "Account update"

        # Body of the email
        body = f"""<p>Please <a href="127.0.0.1/roles/partner/{verification_key}">Click here</a> to confirm your role as partner</p>"""
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")

        return "email sent"
       
    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass
##############################

def send_deletion_email(to_email):
    try:
        # Configure your SMTP server settings
        # Create a gmail fullflaskdemomail
        # Enable (turn on) 2 step verification/factor in the google account manager
        # Visit: https://myaccount.google.com/apppasswords


        # Email and password of the sender's Gmail account
        sender_email = "wrathzeek@gmail.com"
        password = "qxea cqda veji leia"  # If 2FA is on, use an App Password instead

        # Receiver email address
        receiver_email = "wrathzeek@gmail.com"
        
        # Create the email message
        message = MIMEMultipart()
        message["From"] = "Wolt"
        message["To"] = receiver_email
        message["Subject"] = "Account deletion"

        # Body of the email
        body = f"""<p>Your account has been deleted</p>"""
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")

        return "email sent"

    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass



##############################
def send_forgot_password(to_email, user_verification_key):
    try:
        # Configure your SMTP server settings
        # Create a gmail fullflaskdemomail
        # Enable (turn on) 2 step verification/factor in the google account manager
        # Visit: https://myaccount.google.com/apppasswords


        # Email and password of the sender's Gmail account
        sender_email = "wrathzeek@gmail.com"
        password = "qxea cqda veji leia"  # If 2FA is on, use an App Password instead

        # Receiver email address
        receiver_email = "wrathzeek@gmail.com"

        message = MIMEMultipart()
        message["From"] = "Wolt"
        message["To"] = receiver_email
        message["Subject"] = "Reset your password"

        # Body of the email
        body = f"""
        <p>To reset your password, please <a href="http://127.0.0.1/reset-password/{user_verification_key}">click here</a></p>
        """
        message.attach(MIMEText(body, "html"))

        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")

        return "email sent"

    except Exception as ex:
        raise_custom_exception("cannot send email", 500)
    finally:
        pass



##############################


