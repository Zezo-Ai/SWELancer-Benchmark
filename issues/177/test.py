import time
import imaplib
import re
import pytest
import email
from playwright.sync_api import sync_playwright, expect
from playwright.sync_api._context_manager import PlaywrightContextManager
from playwright._impl._browser import Browser
from playwright._impl._page import Page

# Utility function to generate a unique random email for testing
def generate_random_email():
    timestamp = int(time.time())
    return f"freelanceapptest+{timestamp}@gmail.com"

EMAIL = "t1533148@gmail.com" # for example test+1234@gmail.com
PASSWORD = "logb hzkg pkfk kskg" # it will be something like "sdib pxop ovyl uawy"

def get_otp_from_email(username, password, retries=12):
    """
    Read the OTP email and return the OTP code.
    """
    with imaplib.IMAP4_SSL(host="imap.gmail.com") as imap:
        imap.login(username, password)
        for _ in range(1, retries + 1):
            imap.select("inbox")
            status, messages = imap.search(None, "ALL")
            if status == "OK":
                for message_id in reversed(messages[0].split()):
                    status, data = imap.fetch(message_id, "(RFC822)")
                    if status == "OK":
                        email_message = email.message_from_bytes(data[0][1])
                        subject, encoding = email.header.decode_header(email_message["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding)
                        if subject.startswith("Expensify magic sign-in code:"):
                            otp_code = subject.split(":")[-1].strip()
                            return otp_code
        imap.close()
    raise AssertionError("Failed to read the OTP from the email")

# Function to log in a user and complete onboarding steps
def login_user(p: PlaywrightContextManager, first_name="Milan", last_name="T") -> tuple[Browser, Page, str]:
    # Launch Chromium browser in visible mode (non-headless)
    browser = p.chromium.launch(headless=False, args=[
        "--ignore-certificate-errors",
        "--disable-web-security",
        "--disable-features=IsolateOrigins,site-per-process"
    ],
    proxy={"server": "http://localhost:8080"}, slow_mo=1000)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    user_email = EMAIL

    # Step 1: Open the Expensify URL
    page.goto('https://dev.new.expensify.com:8082/concierge')

    # Step 2: Enter the generated email and click continue
    page.locator('input[type="email"]').fill(user_email)
    page.get_by_role("button", name="Continue").click()
    try:
        page.wait_for_selector('button[tabindex="0"]:has-text("Join")', timeout=15000) 
        page.get_by_role("button", name="Join").click()
        page.locator("div").filter(has_text=re.compile(r"^Something else$")).first.click()
        page.locator("body").press("Enter")
        page.wait_for_timeout(1000)

        # Enter first name and last name
        page.locator('input[name="fname"]').fill("Account")
        page.locator('input[name="lname"]').fill("User")
        page.get_by_role("button", name="Continue").last.click()
        page.get_by_role("button", name="Get Started").click()

        page.wait_for_timeout(4000) 
    except:
        # page.locator('input[type="email"]').fill(user_email)
        page.wait_for_timeout(5000)
        otp_code = get_otp_from_email(EMAIL, PASSWORD)
        page.get_by_test_id("SignInPage").get_by_test_id("validateCode").fill("123456")

    return browser, context, page, user_email

# Test to verify opening distance receipt from another workspace opens without issue
def test_open_receipt_different_workspace():
    with sync_playwright() as p:
        browser, context, page, user_email1 = login_user(p)
        page.wait_for_timeout(5000)
        page.get_by_test_id("CustomBottomTabNavigator").get_by_label("Search").last.click()
        page.get_by_test_id("Search").get_by_label("Search").click()
        page.get_by_test_id("search-router-text-input").fill("yin")
        page.get_by_label("yin").last.click()
        expect(page.get_by_text("You haven't created any")).not_to_be_visible()
        context.close()
        browser.close()