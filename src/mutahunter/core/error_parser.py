import re


def extract_error_message(lang: str, fail_message: str) -> str:
    if lang == "python":
        return extract_error_message_python(fail_message)
    elif lang == "java":
        return extract_error_message_java(fail_message)
    elif lang == "go":
        return extract_error_message_go(fail_message)
    else:
        return fail_message.strip()


def extract_error_message_python(fail_message):
    """
    Extracts and returns the error message from the provided failure message.

    Parameters:
        fail_message (str): The failure message containing the error message to be extracted.

    Returns:
        str: The extracted error message from the failure message, or an empty string if no error message is found.

    """
    try:
        # Define a regular expression pattern to match the error message
        MAX_LINES = 20
        pattern = r"={3,} FAILURES ={3,}(.*?)(={3,}|$)"
        match = re.search(pattern, fail_message, re.DOTALL)
        if match:
            err_str = match.group(1).strip("\n")
            err_str_lines = err_str.split("\n")
            if len(err_str_lines) > MAX_LINES:
                # show last MAX_lines lines
                err_str = "...\n" + "\n".join(err_str_lines[-MAX_LINES:])
            return err_str
        return fail_message.strip()
    except Exception as e:
        return fail_message.strip()


def extract_error_message_java(fail_message):
    """
    Extracts and returns the error message from the provided Java Maven failure message.

    Parameters:
        fail_message (str): The failure message containing the error message to be extracted.

    Returns:
        str: The extracted error message from the failure message, or the full message if no specific error message is found.
    """
    try:
        # Define a regular expression pattern to match the error message
        MAX_LINES = 20
        pattern = r"^\[ERROR\] (.*?FAILURE!)$"
        match = re.search(pattern, fail_message, re.MULTILINE | re.DOTALL)
        if match:
            err_str = match.group(1).strip("\n")
            err_str_lines = err_str.split("\n")
            if len(err_str_lines) > MAX_LINES:
                # show last MAX_LINES lines
                err_str = "...\n" + "\n".join(err_str_lines[-MAX_LINES:])
            return err_str
        return fail_message.strip()
    except Exception as e:
        return fail_message.strip()


def extract_error_message_go(fail_message):
    try:
        # Define a regular expression pattern to match the error message
        MAX_LINES = 20
        # Regex pattern to capture error details including method names
        pattern = r"(?i)(--- FAIL: [^\n]*\n.*?)(?=\n\[|--- FAIL:|\Z)"
        matches = re.findall(pattern, fail_message, re.MULTILINE | re.DOTALL)

        if matches:
            err_str = ""
            for match in matches:
                err_str += match.strip("\n") + "\n"

            err_str_lines = err_str.split("\n")
            if len(err_str_lines) > MAX_LINES:
                # Show last MAX_LINES lines
                err_str = "...\n" + "\n".join(err_str_lines[-MAX_LINES:])
            return err_str.strip()
        return fail_message.strip()
    except Exception as e:
        return fail_message.strip()
