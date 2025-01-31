"""Test utilities for quipucords' UI tests."""
import os

import pytest
from selenium import webdriver
from widgetastic.browser import Browser

from .utils import create_credential
from .views import LoginView
from camayoc import config
from camayoc.tests.qpc.cli.utils import clear_all_entities
from camayoc.ui import Client as UIClient
from camayoc.ui.session import BasicSession
from camayoc.utils import get_qpc_url
from camayoc.utils import uuid4


def pytest_collection_modifyitems(config, items):
    """Check for presence of driver for selenium.

    If no driver option is present then UI test should be skipped.
    UI tests should be marked with @pytest.mark.ui
    """
    if not os.environ.get("SELENIUM_DRIVER", None):
        skip_ui = pytest.mark.skip(reason="need --driver option to run UI tests")
        for item in items:
            if "selenium_browser" in item.fixturenames:
                item.add_marker(skip_ui)


def pytest_exception_interact(node, call, report):
    ui_client = node.funcargs.get("ui_client", None)
    if not ui_client:
        return
    print("List of previous successfull actions:")
    zeroes = len(str(len(ui_client.session.history)))
    for step, record in enumerate(ui_client.session.history):
        step_num = str(step).zfill(zeroes)
        print(f"{step_num}: {record}")


@pytest.fixture(scope="module")
def selenium_browser(request):
    """Selenium instance.

    See README for configuration of remote browser containers.
    """
    # Default to chrome for UI testing.
    driver_type = os.environ.get("SELENIUM_DRIVER", "chrome").lower()
    debug_mode = os.environ.get("SELENIUM_DEBUG", "false").lower() == "true"
    if driver_type == "chrome":
        chrome_options = webdriver.ChromeOptions()
        if not debug_mode:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--allow-insecure-localhost")
        driver = webdriver.Remote(
            "http://127.0.0.1:4444/wd/hub",
            desired_capabilities=chrome_options.to_capabilities(),
        )
    elif driver_type == "firefox":
        firefox_options = webdriver.firefox.options.Options()
        if debug_mode:
            firefox_options.add_argument("--headless")
        driver = webdriver.Remote(
            "http://127.0.0.1:4444/wd/hub",
            desired_capabilities=firefox_options.to_capabilities(),
        )
    else:
        raise ValueError(f"Unsupported SELENIUM_DRIVER provided: {driver_type}")

    driver.get(get_qpc_url())
    driver.maximize_window()
    yield Browser(driver)
    driver.close()


@pytest.fixture(scope="module")
def qpc_login(browser):
    """Log the user into the dashboard."""
    login = LoginView(browser)
    login.username.fill("admin")
    login.password.fill("pass")
    login.login.click()
    assert browser.selenium.title == "Entitlements Reporting"


@pytest.fixture(scope="module")
def credentials(browser, qpc_login):
    """Allocate dummy credentials to be used with sources.

    Yields a dict of the name of a network, Satellite, and vCenter
    credential for use with sources.
    """
    # Credential type is a case-sensitive parameter and matches UI text
    names = {
        "Network": uuid4(),
        "Network2": uuid4(),
        "Satellite": uuid4(),
        "VCenter": uuid4(),
    }
    username = uuid4()
    password = uuid4()

    options = {
        "name": (names["Network"]),
        "username": username,
        "password": password,
        "source_type": "Network",
    }
    create_credential(browser, options)
    options["name"] = names["Network2"]
    create_credential(browser, options)
    options["name"] = names["Satellite"]
    options["source_type"] = "Satellite"
    create_credential(browser, options)
    options["name"] = names["VCenter"]
    options["source_type"] = "VCenter"
    create_credential(browser, options)
    yield names
    # Some tests are flaky, so we need to do a full clear
    # to garbage-collect resources from failed calls.
    # database lock sometimes occurs, so we attempt this twice
    # quipucords/quipucords/issues/1275
    try:
        clear_all_entities()
    except Exception:
        clear_all_entities()


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    extra_context_args = {}
    verify_ssl = config.get_config().get("qpc", {}).get("ssl-verify", False)
    if not verify_ssl:
        extra_context_args["ignore_https_errors"] = True

    return {**browser_context_args, **extra_context_args}


@pytest.fixture
def ui_client(page):
    client_session = BasicSession()
    client = UIClient(driver=page, session=client_session)
    yield client
