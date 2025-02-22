import sys, os

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, base_path)

from locale import currency
import time
from playwright.sync_api import sync_playwright, expect
from playwright.sync_api._context_manager import PlaywrightContextManager
from playwright._impl._browser import Browser
from playwright._impl._page import Page

static_email = "testuserexpensify1+45@gmail.com"

def test_delay_submission_toggle():

    from utils.trace_cleaner import trace_cleaner

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            slow_mo=1000,
            args=["--disable-web-security", "--disable-features=IsolateOrigins,site-per-process"]
        )
        context = browser.new_context()


        context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = context.new_page()

        try:
            user_email = static_email

            page.goto('https://dev.new.expensify.com:8082/')


            page.locator('input[type="email"]').fill(user_email)
            page.locator('button[tabindex="0"]').click()


            try:
                page.locator('button[tabindex="0"]').click()
                page.wait_for_timeout(1000)
            except Exception:
                pass


            page.locator("text='Track and budget expenses'").click()
            page.get_by_role("button", name="Continue").click()


            page.locator('input[name="fname"]').fill("Milan")
            page.locator('input[name="lname"]').fill("T")
            page.get_by_role("button", name="Continue").last.click()


            plus_icon = page.locator('button[aria-label="Start chat (Floating action)"]')
            plus_icon.click()

            new_workspace_button = page.locator('div[aria-label="New workspace"]')
            new_workspace_button.click()


            page_feature = page.locator('div[aria-label="More features"]')
            page_feature.click()


            workflows = page.locator('button[aria-label="Configure how spend is approved and paid."]')
            workflows.click()

            workflow_setting = page.locator('div[aria-label="Workflows"]')
            workflow_setting.click()


            delay_submission = page.locator('button[aria-label="Delay expense submissions based on a custom schedule, or keep this option disabled to maintain realtime spend visibility."]')
            delay_submission.click()


            submission_frequency = page.get_by_text("Weekly")
            submission_frequency.click()

            change_manual_freq = page.locator('button[aria-label="Manually"]')
            change_manual_freq.click()


            is_delay_toggle_off = page.locator(
                'button[aria-label="Delay expense submissions based on a custom schedule, or keep this option disabled to maintain realtime spend visibility."]'
            )
            aria_checked_value = is_delay_toggle_off.get_attribute('aria-checked')

            if aria_checked_value == "false":
                assert False, "Delay submissions turns off if the Submission frequency is set to Manually"
            else:
                assert True, "Delay submissions does not turn off if the Submission frequency is set to Manually"

            page.wait_for_timeout(2000)

        finally:

            context.tracing.stop(path="/app/expensify/user_tool/output_browser1.zip")

            trace_cleaner("/app/expensify/user_tool/output_browser1.zip")
            browser.close()
