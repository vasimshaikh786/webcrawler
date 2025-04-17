import re
import streamlit as st

def find_phone_numbers(html_content, current_url):
    """Finds phone numbers in the HTML content (more comprehensive pattern)."""
    phone_number_pattern = re.compile(
        r'''
        (\+?\d{1,4}[-\s.]?)?   # Optional country code with separator
        \(?\d{2,4}\)?           # Optional area code in parentheses
        [-\s.]?                # Optional separator
        \d{2,4}                 # First part of the number
        [-\s.]?                # Optional separator
        \d{3,4}                 # Last part of the number
        ([-\s.]?\d{3,5})?       # Optional extension
        ''',
        re.VERBOSE | re.IGNORECASE
    )
    phone_numbers = set(re.findall(phone_number_pattern, html_content))
    # Further filtering to remove very short matches and potential noise
    valid_phone_numbers = [number for number in phone_numbers if len("".join(filter(str.isdigit, number))) >= 7]
    return [{"number": number, "location": current_url} for number in valid_phone_numbers]
