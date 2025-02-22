import sys, os

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, base_path)

import email
import imaplib
import time

from playwright.sync_api import TimeoutError, expect, sync_playwright


EMAIL_USERNAME = "expensifytesting1@gmail.com"
EMAIL_PASSWORD = "redx tbmr hzpc rbzr"


EMAIL_USERNAME_POSTFIX = "46528"


def generate_user_email(user_id=None):
    """
    Generate an email address for a user login.
    """
    temp = EMAIL_USERNAME.rsplit("@", 1)
    username = temp[0].strip()
    domain = temp[1].strip()
    return f"{username}+{EMAIL_USERNAME_POSTFIX}{user_id or ''}@{domain}"


def clear_inbox(username, password):
    """
    Delete all the messages from the Inbox.
    """

    return
    with imaplib.IMAP4_SSL(host="imap.gmail.com") as imap:
        imap.login(username, password)
        imap.select("inbox")
        imap.store("1:*", "+FLAGS", "\\Deleted")
        imap.expunge()
        imap.close()


def get_otp_from_email(username, password, retries=12, delay=5):
    """
    Read the OTP email and return the OTP code.
    """

    return "123456"
    with imaplib.IMAP4_SSL(host="imap.gmail.com") as imap:
        imap.login(username, password)
        for i in range(1, retries + 1):
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
            time.sleep(delay)
        imap.close()
    raise AssertionError("Failed to read the OTP from the email")



def login_member(p, member_first_name: str, member_last_name: str) -> tuple:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-web-security", "--disable-features=IsolateOrigins,site-per-process"],
    )
    context = browser.new_context()
    page = context.new_page()

    user_email = generate_user_email()

    page.goto("https://dev.new.expensify.com:8082/")
    clear_inbox(EMAIL_USERNAME, EMAIL_PASSWORD)
    page.locator('input[type="email"]').fill(user_email)
    page.locator('button[tabindex="0"]').click()

    try:
        page.locator('button[tabindex="0"]').click()
    except Exception:
        pass


    try:
        expect(page.get_by_test_id("SignInPage").get_by_test_id("validateCode")).to_be_visible(timeout=5000)
    except AssertionError:

        page.get_by_test_id("SignInPage").get_by_role("button", name="Join").click()
    else:

        otp_code = get_otp_from_email(EMAIL_USERNAME, EMAIL_PASSWORD)
        page.get_by_test_id("SignInPage").get_by_test_id("validateCode").fill(otp_code)
        try:
            page.get_by_test_id("SignInPage").get_by_role("button", name="Sign in").click(timeout=2000)
        except (AssertionError, TimeoutError):
            pass

    try:
        expect(page.get_by_text("What do you want to do today?")).to_be_visible(timeout=5000)
    except AssertionError:
        pass
    else:

        page.get_by_label("Track and budget expenses").click()
        page.locator('input[name="fwork"]').fill(f"Work_{int(time.time())}")
        page.get_by_role("button", name="Continue").last.click()
        page.get_by_role("textbox", name="First name").fill(member_first_name)
        page.get_by_role("textbox", name="Last name").fill(member_last_name)
        page.get_by_role("button", name="Continue").click()

    expect(page.get_by_test_id("BaseSidebarScreen")).to_be_visible(timeout=10000)

    return browser, page, user_email


def add_member(page):
    page.get_by_label("My settings").click()
    page.get_by_test_id("InitialSettingsPage").get_by_label("Workspaces").get_by_text("Workspaces").click()

    test_workspace = "WS Test"
    existing_workspaces = [
        item.split("\n")[0].strip()
        for item in page.get_by_test_id("WorkspacesListPage").get_by_label("row", exact=True).all_inner_texts()
    ]
    if test_workspace not in existing_workspaces:
        page.get_by_test_id("WorkspacesListPage").get_by_role("button", name="New workspace").first.click()
        page.wait_for_timeout(2000)
        page.get_by_test_id("WorkspacePageWithSections").get_by_text("Name", exact=True).click()
        page.get_by_test_id("WorkspaceNamePage").get_by_role("textbox").fill(test_workspace)
        page.get_by_test_id("WorkspaceNamePage").get_by_role("button", name="Save").click()
        page.wait_for_timeout(2000)
        page.get_by_test_id("WorkspaceInitialPage").get_by_role("button", name="Back").click()
    page.get_by_test_id("WorkspacesListPage").get_by_label("row").get_by_text(test_workspace).first.click()
    page.get_by_text("More features").click()

    try:
        expect(page.get_by_label("Set up custom fields for")).to_be_checked(timeout=1000)
    except (AssertionError, TimeoutError):
        page.get_by_label("Set up custom fields for").click()
        page.get_by_role("button", name="Upgrade").click()
        page.get_by_role("button", name="Got it, thanks").click()
    page.get_by_test_id("WorkspaceInitialPage").get_by_text("Report fields").click()
    field_name = f"Filed_{int(time.time())}"
    page.get_by_role("button", name="Add field").click()
    page.get_by_test_id("CreateReportFieldsPage").get_by_text("Name").click()
    page.get_by_role("textbox", name="Name").fill(field_name)
    page.get_by_test_id("TextSelectorModal").get_by_role("button", name="Save").click()
    page.get_by_test_id("CreateReportFieldsPage").get_by_text("Type").click()
    page.get_by_test_id("selection-list").get_by_label("List").click()
    page.get_by_role("button", name="Save").click()
    page.locator(f"#field_id_{field_name.upper()}").click()
    page.get_by_text("List values").click()
    page.get_by_role("button", name="Add value").click()
    page.get_by_role("textbox", name="Value").fill("c479")
    page.get_by_role("button", name="Save").click()
    page.get_by_role("button", name="Add value").click()
    page.get_by_role("textbox", name="Value").fill("b789")
    page.get_by_role("button", name="Save").click()
    page.get_by_role("button", name="Add value").click()
    page.get_by_role("textbox", name="Value").fill("t963")
    page.get_by_role("button", name="Save").click()

    first_list_value = page.locator('div[data-testid="selection-list"]').nth(1)
    assert (
        first_list_value.inner_text() == "b789\nEnabled\nc479\nEnabled\nt963\nEnabled"
    ), "The first list value is not 'b789'"


def test_run(admin_first_name="Yagna", admin_last_name="Sai", member_first_name="Sai", member_last_name="Yagna"):
    with sync_playwright() as p:
        browser_member, page_member, user_email = login_member(p, member_first_name, member_last_name)
        add_member(page_member)
        browser_member.close()


if __name__ == "__main__":
    test_run()
