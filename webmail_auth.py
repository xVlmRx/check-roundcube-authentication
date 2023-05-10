# -*- coding: utf-8 -*-

import re
import requests
from bs4 import BeautifulSoup


MAILNODE_NUMBER = <some_text>

MAILBOX_LOGIN = "<some_text>{}@<some_text>".format(MAILNODE_NUMBER)
MAILBOX_PASSWORD = "<some_text>{}<some_text>".format(MAILNODE_NUMBER)

ROUNDCUBE_MAIN_URL = "https://web{}.<some_text>/".format(MAILNODE_NUMBER)
LOCATION_LOGIN = "?_task=login"
LOCATION_LOGOUT = "?_task=logout&_token="


def get_session_id(responce, cookie_name):
    cookie_value = responce.cookies[cookie_name]

    return cookie_value


def get_token_from_body(responce):
    parse_data = BeautifulSoup(responce.text, 'html.parser')
    hidden_tags = parse_data.find_all("input", type="hidden")
    for tag in hidden_tags:
        token = parse_data.find('input', {'name': '_token'}).get('value')
        if token:
            return token
        print("Another try search token")


def check_page_content(responce, parse_tag, parse_class, pattern):
    soup = BeautifulSoup(responce.text, 'html.parser')
    button = soup.find(parse_tag, class_=parse_class)
    if button.text == pattern:
        print("Pattern {} detected. Page successfully loaded.".format(pattern))
        return True
    else:
        print("Pattern {} not detected. Page not loaded correctly.".format(pattern))
        return False


if __name__ == '__main__':

    # Create new requests session
    new_session = requests.session()

    # Load Roundcube Login page
    print("Load Roundcube main page")
    try:
        load_page = new_session.post(ROUNDCUBE_MAIN_URL, timeout=10)
    except Exception as err:
        print("Oops! Something went wrong!", str(err))
        exit(0)

    # Check load login page
    check_page_content(load_page, 'button', 'button', 'Войти')

    # Get session ID before start login
    first_session_id = get_session_id(load_page, 'beget_webmail_session_id')
    print("Before login session ID:", first_session_id)

    # Get token from page body before start login
    first_token = get_token_from_body(load_page)
    print("Before login token value:", first_token)

    # Set headers for login
    headers = {
        'cookie': 'beget_webmail_session_id='+first_session_id,
    }

    # Set data for login
    data = {
        "_token": first_token,
        "_task": "login",
        "_action": "login",
        "_user": MAILBOX_LOGIN,
        "_pass": MAILBOX_PASSWORD
    }

    # Login to mailbox
    print("Login to mailbox")
    try:
        login = new_session.post(ROUNDCUBE_MAIN_URL+LOCATION_LOGIN, data=data, headers=headers, allow_redirects=True)
    except Exception as err:
        print("Oops! Something went wrong!", str(err))
        exit(0)

    # Check redirect to mailbox and get new ids and tokens
    if login.history:
        print("Request was redirected")
        for resp in login.history:
            print("Logout status&URI")
            print(resp.status_code, resp.url)
            after_login_session_id = get_session_id(resp, 'beget_webmail_session_id')
            after_login_webmail_sessauth = get_session_id(resp, 'beget_webmail_sessauth')
        print("Response destination:")
        print(login.status_code, login.url)
        after_login_token = re.search(r"_token=(.*)$", login.url).group(1)
        print("After login session ID:", after_login_session_id)
        print("After login Webmail sessauth cookie:", after_login_webmail_sessauth)
        print("After login token:", after_login_token)
    else:
        print("Request was not redirected")

    after_login_headers = {
        'cookie': "beget_webmail_session_id={}; beget_webmail_sessauth={}"
        .format(after_login_session_id,
                after_login_webmail_sessauth)
    }

    # Check load mailbox page
    check_page_content(login, 'span', 'header-title username', MAILBOX_LOGIN)

    print("Start Logout")
    try:
        logout = new_session.get(ROUNDCUBE_MAIN_URL+LOCATION_LOGOUT+after_login_token, headers=after_login_headers, timeout=10)
    except Exception as err:
        print("Oops! Something went wrong!", str(err))
        exit(0)
    if logout.history:
        print("Request was redirected")
        for respout in logout.history:
            print("Logout status&URI")
            print(respout.status_code, respout.url)
        print("Response destination:")
        print(logout.status_code, logout.url)
    else:
        print("Request was not redirected")

    # Check load login page after logout
    check_page_content(load_page, 'button', 'button', 'Войти')
