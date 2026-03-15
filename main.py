"""
Comedy Driving Company - Course Automation
Logs in, goes through each module, handles timers, stops at quizzes.
"""
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager

try:
    from config import EMAIL, PASSWORD, SECURITY_ANSWERS
except ImportError:
    EMAIL = "youremail@gmail.com"
    PASSWORD = "your pass"
    SECURITY_ANSWERS = {"states": "2", "car_age": "6-10"}

# URLs
BASE_URL = "https://www.comedydrivingcompany.com"
LOGIN_URL = f"{BASE_URL}/user/login"
DASHBOARD_URL = f"{BASE_URL}/dashboard"

# Wait timeouts
WAIT_TIMEOUT = 15
ACTION_DELAY = 0.5  # Seconds between each action
ELEMENT_WAIT = 10   # Max seconds to wait for elements to load


def log(msg: str) -> None:
    print(f"[*] {msg}")


def action_delay() -> None:
    """Wait 0.5 seconds between actions."""
    time.sleep(ACTION_DELAY)


def wait_and_click(driver, by, selector, description: str = "element") -> bool:
    """Wait for element to be clickable, then click. Returns True if clicked."""
    try:
        elem = WebDriverWait(driver, ELEMENT_WAIT).until(
            EC.element_to_be_clickable((by, selector))
        )
        action_delay()
        elem.click()
        log(f"Clicked: {description}")
        action_delay()
        return True
    except Exception:
        return False


def setup_driver():
    """Initialize Chrome with webdriver-manager."""
    service = Service(ChromeDriverManager().install())
    options = Options()
    # Uncomment to run headless: options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    return driver


def _find_element(driver, selectors):
    """Find first matching element. Returns element or None."""
    for by, selector in selectors:
        try:
            return WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((by, selector))
            )
        except Exception:
            continue
    return None


def login(driver) -> bool:
    """Log in to Comedy Driving Company."""
    log("Navigating to login page...")
    driver.get(LOGIN_URL)
    action_delay()

    time.sleep(1)
    action_delay()

    # Exact selectors: input#loginemail, input#loginpass, button.btn-login
    email_input = _find_element(driver, [
        (By.ID, "loginemail"),
        (By.CSS_SELECTOR, "input[name='loginemail']"),
    ])
    if not email_input:
        log("ERROR: Could not find email input (#loginemail)")
        return False

    password_input = _find_element(driver, [
        (By.ID, "loginpass"),
        (By.CSS_SELECTOR, "input[name='loginpass']"),
    ])
    if not password_input:
        log("ERROR: Could not find password input (#loginpass)")
        return False

    log("Entering credentials...")
    for attempt in range(3):
        try:
            email_input = _find_element(driver, [(By.ID, "loginemail"), (By.CSS_SELECTOR, "input[name='loginemail']")])
            if email_input:
                email_input.click()
                action_delay()
                email_input.clear()
                action_delay()
                email_input.send_keys(EMAIL)
            action_delay()

            password_input = _find_element(driver, [(By.ID, "loginpass"), (By.CSS_SELECTOR, "input[name='loginpass']")])
            if password_input:
                password_input.click()
                action_delay()
                password_input.clear()
                action_delay()
                password_input.send_keys(PASSWORD)
            break
        except StaleElementReferenceException:
            action_delay()
            continue
    action_delay()

    # Log In button: button.btn-normal.btn-login
    login_btn = _find_element(driver, [
        (By.CSS_SELECTOR, "button.btn-login"),
        (By.CSS_SELECTOR, "button.btn-normal.btn-login"),
        (By.XPATH, "//button[@type='submit' and contains(., 'Log In')]"),
    ])
    if login_btn:
        WebDriverWait(driver, ELEMENT_WAIT).until(EC.element_to_be_clickable(login_btn))
        action_delay()
        login_btn.click()
    else:
        password_input = _find_element(driver, [(By.ID, "loginpass")])
        if password_input:
            password_input.send_keys(Keys.RETURN)

    action_delay()
    log("Login submitted.")
    return True


def go_to_dashboard_and_open_ongoing_module(driver) -> bool:
    """Go to dashboard, find ongoing module via ongoing.jpg, click chapter link, then section link."""
    log("Navigating to dashboard...")
    driver.get(DASHBOARD_URL)
    action_delay()

    WebDriverWait(driver, ELEMENT_WAIT).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    action_delay()

    # Find ongoing module: img with ongoing.jpg, then get related chapter link
    # XPath: from img[src*='ongoing.jpg'] find ancestor container and the chapter <a> link
    try:
        chapter_link = driver.find_element(
            By.XPATH,
            "//img[contains(@src,'ongoing.jpg')]/ancestor::*//a[contains(@href,'/lesson/adult-drivers-education-chapter')]"
        )
        if chapter_link.is_displayed() and chapter_link.is_enabled():
            log("Found ongoing module (ongoing.jpg), clicking chapter link...")
            WebDriverWait(driver, ELEMENT_WAIT).until(EC.element_to_be_clickable(chapter_link))
            action_delay()
            chapter_link.click()
            action_delay()
        else:
            raise Exception("Chapter link not visible")
    except Exception as e:
        log(f"Could not find ongoing module via ongoing.jpg: {e}")
        # Fallback: try first a[href*='adult-drivers-education-chapter'] that's not completed
        try:
            links = driver.find_elements(By.XPATH, "//a[contains(@href,'/lesson/adult-drivers-education-chapter')]")
            for link in links:
                if link.is_displayed():
                    log("Fallback: clicking first chapter link...")
                    WebDriverWait(driver, ELEMENT_WAIT).until(EC.element_to_be_clickable(link))
                    action_delay()
                    link.click()
                    action_delay()
                    break
        except Exception:
            pass

    action_delay()

    # Chapter page: click section link a[href*="/lesson-section/"]
    try:
        section_link = WebDriverWait(driver, ELEMENT_WAIT).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='/lesson-section/']"))
        )
        if section_link.is_displayed():
            log(f"Clicking section link: {section_link.text.strip()[:50]}...")
            action_delay()
            section_link.click()
            action_delay()
            return True
    except Exception as e:
        log(f"Could not find section link: {e}")

    log("Could not find section link - may already be on section page. Continuing...")
    return True


def parse_timer_seconds(page_source: str) -> int | None:
    """Parse remaining time from page. Returns seconds or None."""
    # Primary: "You can take the quiz in 26 minutes and 1 seconds."
    m = re.search(r"(\d+)\s*minutes?\s*and\s*(\d+)\s*seconds?", page_source, re.I)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))

    # Fallback: "4:32" or "04:32" (mm:ss)
    m = re.search(r"(\d{1,2}):(\d{2})", page_source)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))

    # Fallback: "5 minutes" or "wait 5 min"
    m = re.search(r"(?:wait\s+)?(\d+)\s*min", page_source, re.I)
    if m:
        return int(m.group(1)) * 60

    # Fallback: "300 seconds"
    m = re.search(r"(\d+)\s*sec", page_source, re.I)
    if m:
        return int(m.group(1))

    return None


def is_quiz_page(driver) -> bool:
    """Detect if current page is a quiz."""
    source = driver.page_source.lower()
    url = driver.current_url.lower()

    quiz_indicators = [
        "quiz",
        "question 1 of",
        "submit quiz",
        "multiple choice",
        "select your answer",
        "choose the correct",
    ]
    return any(ind in source or ind in url for ind in quiz_indicators)


def scroll_content(driver) -> None:
    """Scroll through page content (some courses track scroll)."""
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        action_delay()
        driver.execute_script("window.scrollTo(0, 0);")
        action_delay()
    except Exception:
        pass


def run_section_loop(driver) -> None:
    """Loop: view content, wait for timers, click Next section. Stops at quiz."""
    log("Entering section loop...")
    max_iterations = 200  # Safety limit
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        log(f"--- Iteration {iteration} ---")
        log(f"URL: {driver.current_url}")

        # Wait for page to load
        WebDriverWait(driver, ELEMENT_WAIT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        action_delay()

        # Check for quiz first
        if is_quiz_page(driver):
            log("QUIZ DETECTED - Stopping. Complete the quiz manually.")
            return

        # Scroll content
        scroll_content(driver)
        action_delay()

        # Check for timer / wait message
        source = driver.page_source
        wait_seconds = parse_timer_seconds(source)

        if wait_seconds and wait_seconds > 0:
            log(f"Timer detected: waiting {wait_seconds} seconds ({wait_seconds // 60}m {wait_seconds % 60}s)")
            time.sleep(wait_seconds)
            action_delay()
            action_delay()  # Buffer after timer

        # Find "Go to Next Section" button - exact: a.btn.btn-success.next-section
        next_section_selectors = [
            (By.CSS_SELECTOR, "a.next-section"),
            (By.CSS_SELECTOR, "a.btn-success.next-section"),
            (By.XPATH, "//a[contains(@class,'next-section') and contains(.,'Go to Next Section')]"),
            (By.PARTIAL_LINK_TEXT, "Go to Next Section"),
            # Fallbacks
            (By.XPATH, "//a[contains(., 'Next section') or contains(., 'Next Section')]"),
            (By.PARTIAL_LINK_TEXT, "Next section"),
            (By.PARTIAL_LINK_TEXT, "Next Section"),
        ]
        clicked = False
        for by, selector in next_section_selectors:
            try:
                elements = driver.find_elements(by, selector)
                for elem in elements:
                    try:
                        if elem.is_displayed() and elem.is_enabled():
                            WebDriverWait(driver, ELEMENT_WAIT).until(
                                EC.element_to_be_clickable(elem)
                            )
                            action_delay()
                            elem.click()
                            log("Clicked Next section / Continue")
                            clicked = True
                            action_delay()
                            break
                    except Exception:
                        continue
                if clicked:
                    break
            except Exception:
                continue

        if not clicked:
            log("No Next section button found. May be at end or quiz. Stopping.")
            if is_quiz_page(driver):
                log("Quiz confirmed - stop here.")
            return

        action_delay()


def main():
    driver = None
    try:
        log("Starting Comedy Driving Course automation...")
        driver = setup_driver()

        if not login(driver):
            log("Login failed. Check credentials and selectors.")
            input("Press Enter to close...")
            return

        action_delay()

        go_to_dashboard_and_open_ongoing_module(driver)
        action_delay()

        run_section_loop(driver)

        log("Automation finished. Browser will stay open.")
        input("Press Enter to close the browser...")
    except KeyboardInterrupt:
        log("Interrupted by user.")
    except Exception as e:
        log(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to close...")
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
