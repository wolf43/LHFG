#!/usr/bin/env python2.7
"""Tests for SSL project."""
import json
from time import sleep
import argparse
from pprint import pprint
from termcolor import colored
import requests  # http://docs.python-requests.org/en/latest/
import validators  # https://validators.readthedocs.org/en/latest/


DICT_FOR_RESULTS = {}
DICT_COMPLETE_RESPONSE = {}


def check_if_valid_url(url_to_test):
    """Very lenient test for validity of a url using validators."""
    if validators.url(url_to_test) or validators.domain(url_to_test):
        print "\n\nValid url: " + str(url_to_test) + "\nStarting test"
        return True
    else:
        print "\nError"
        print "Url: " + str(url_to_test) + " ain't valid"
        DICT_FOR_RESULTS[INPUT_URL]['SSL labs error'] = True
        return False


def read_file(path_to_file):
    """Read file and return dict."""
    with open(path_to_file) as data_file:
        data = data_file.read().splitlines()
    print data
    return data


def get_cl_arguments():
    """Get the command line arguments passed by user."""
    parser = argparse.ArgumentParser(prog='SSL tester', description='Suite of SSL tests')
    parser.add_argument('-i', '--input_file', nargs='?', help='Input file')
    parser.add_argument('-u', '--input_url', nargs='?', help='Input url')
    parser.add_argument('-o', '--output_file', nargs='?', help='Output file')
    args = parser.parse_args()
    return vars(args)['input_file'], vars(args)['input_url'], vars(args)['output_file']


def wait_for_seconds(time_in_sec):
    """The function takes in time in seconds and goes to sleep for that time."""
    print "Waiting for " + str(time_in_sec) + " seconds"
    sleep(time_in_sec)
    print "Waited for " + str(time_in_sec) + " seconds"


def result_from_cache(url_to_test):
    """Check if the results are in SSL labs cache."""
    parameters = {'host': url_to_test, 'fromCache': 'on', 'all': 'done'}
    try:
        response_from_ssl_labs = requests.get(
            "https://api.ssllabs.com/api/v2/analyze",
            params=parameters)
    except Exception as exception:
        print "Error occured when making a request to " + str(url_to_test) + "\nExiting now"
        print "Error: " + str(exception.__doc__)
        print "Details: " + str(exception.message)
    if check_if_response_has_errors(response_from_ssl_labs) is False:
        json_parsed_full_response = json.loads(response_from_ssl_labs.text)
        while json_parsed_full_response['status'] != 'READY':
            print "Result not in cache\nAPI is not ready"
            wait_for_seconds(180)
            response_from_ssl_labs = requests.get(
                "https://api.ssllabs.com/api/v2/analyze", params=parameters)
            if check_if_response_has_errors(response_from_ssl_labs) is True:
                return None
            json_parsed_full_response = json.loads(response_from_ssl_labs.text)
        return json_parsed_full_response
    else:
        return None


def force_new_scan(url_to_test):
    """Force a new scan for a host on SSL labs."""
    check_if_valid_url(url_to_test)
    print "Forcing a new scan for: " + str(url_to_test)
    parameters = {'host': url_to_test, 'startNew': 'on', 'all': 'done'}
    response_from_ssl_labs = requests.get(
        "https://api.ssllabs.com/api/v2/analyze",
        params=parameters)
    check_if_response_has_errors(response_from_ssl_labs)
    # First run of force scan resulted in 90 + 60 + 60 + 60 sec before success,
    # adding 3 min delay before chcking API after forced rescan
    wait_for_seconds(180)
    json_parsed_full_response = scan_without_cache_or_force(url_to_test)
    return json_parsed_full_response


def scan_without_cache_or_force(url_to_test):
    """Just run a scan without any special requests(not just cache, don't force a new one)."""
    check_if_valid_url(url_to_test)
    parameters = {'host': url_to_test, 'all': 'done'}
    response_from_ssl_labs = requests.get(
        "https://api.ssllabs.com/api/v2/analyze",
        params=parameters)
    check_if_response_has_errors(response_from_ssl_labs)
    json_parsed_full_response = json.loads(response_from_ssl_labs.text)
    while json_parsed_full_response['status'] != 'READY':
        print "Result not in cache\nAPI is not ready"
        wait_for_seconds(180)
        response_from_ssl_labs = requests.get(
            "https://api.ssllabs.com/api/v2/analyze", params=parameters)
        check_if_response_has_errors(response_from_ssl_labs)
        json_parsed_full_response = json.loads(response_from_ssl_labs.text)
    return json_parsed_full_response


def check_if_response_has_errors(response):
    """https://github.com/ssllabs/ssllabs-scan/blob/stable/ssllabs-api-docs.md has list of errors."""
    json_parsed_full_response = json.loads(response.text)
    if response.status_code == 200 and json_parsed_full_response['status'] != 'ERROR':
        return False
    elif response.status_code == 200 and json_parsed_full_response['status'] == 'ERROR':
        print "Error"
        print "API retured 200:Error\nMost likely reason: hostname doesn't seem right"
        DICT_FOR_RESULTS[INPUT_URL]['SSL labs error'] = True
        return True
    elif response.status_code == 429:
        print "Error"
        print "Client request rate too high"
        DICT_FOR_RESULTS[INPUT_URL]['SSL labs error'] = True
        return False
    elif response.status_code == 400:
        print "Error"
        print "Invalid parameters\nCheck parameters and try again"
        DICT_FOR_RESULTS[INPUT_URL]['SSL labs error'] = True
    elif response.status_code == 503:
        print "Error"
        print "Service is not available"
        DICT_FOR_RESULTS[INPUT_URL]['SSL labs error'] = True
        return True
    elif response.status_code == 529:
        print "Error"
        print "Service is overloaded"
        DICT_FOR_RESULTS[INPUT_URL]['SSL labs error'] = True
        return False
    else:
        print "Error"
        print "Unexpected response\nStatus: " + str(response.status_code)
        print "Response text:\n" + str(response.text())


def print_json_parsed_response(json_parsed_full_response):
    """The prints the json object retured by ssl labs nicely."""
    print "Status: " + str(json_parsed_full_response['status'])
    print json.dumps(json_parsed_full_response, indent=4)


def get_ssl_labs_grade(json_parsed_full_response):
    """Get SSL labs grade."""
    count_grade_less_than_a = 0
    try:
        grade_list = []
        for i in json_parsed_full_response['endpoints']:
            grade_list.append(i['grade'])
            if "A" not in i['grade']:
                print colored("Grade: ", "red") + colored(str(i['grade']), "red")
                count_grade_less_than_a += 1
        if count_grade_less_than_a == 0:
            DICT_FOR_RESULTS[INPUT_URL]['grade_test'] = "Passed"
            print colored("Test PASSED: SSL labs grade A for all endpoints", "green")
        else:
            DICT_FOR_RESULTS[INPUT_URL]['grade_test'] = "Failed"
            print colored("Test FAILED: SLL labs grade not A for ", "red") + colored(str(count_grade_less_than_a), "red") + colored(" endpoints", "red")
        DICT_FOR_RESULTS[INPUT_URL]['grade'] = grade_list
    except KeyError as key_error:
        print "Key error: " + str(key_error) + "\nThe response object format is not correct"
        print "Please make sure this host exists and has SSL setup"
        DICT_FOR_RESULTS[INPUT_URL]['grade_test'] = "Error"


def ios_ats_test(json_parsed_full_response):
    """Test if errors with ios9 ats - https://developer.apple.com/library/ios/releasenotes/General/WhatsNewIniOS/Articles/iOS9.html."""
    count_of_endpoints_with_ats_errors = 0
    try:
        for i in json_parsed_full_response['endpoints']:
            for j in i['details']['sims']['results']:
                if j['client']['name'] == "Apple ATS":
                    if j['errorCode'] != 0:
                        count_of_endpoints_with_ats_errors += 1
                    # -------------Test case failed-----------------
                else:
                    pass
                    # +++++++++++++Test case passed++++++++++++++++++
        if count_of_endpoints_with_ats_errors == 0:
            DICT_FOR_RESULTS[INPUT_URL]['Apple ATS'] = "All endpoints passed"
            print colored("TEST PASSED: All endpoints for host " + str(json_parsed_full_response['host']) + " passed Apple ATS test", "green")
        else:
            DICT_FOR_RESULTS[INPUT_URL]['Apple ATS'] = str(count_of_endpoints_with_ats_errors) + " endpoints failed"
            print colored("TEST FAILED: Total number of endpoints with Apple ATS test fail: " + str(count_of_endpoints_with_ats_errors), "red")
    except KeyError as key_error:
        print "Key error: " + str(key_error) + "\nThe response object format is not correct"
        print "Please make sure this host exists and has SSL setup"
        DICT_FOR_RESULTS[INPUT_URL]['Apple ATS'] = "Error"


def get_response_ssl_error_exception(url_to_test):
    """Make request and get reponse/handle any exceptions."""
    # Some domains(google.com) don't redirect to https if the user agent is not present
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/48.0.2564.103 Safari/537.36'}
    response = requests.get(url_to_test, headers=headers, timeout=30)
    return response


def get_response_supress_ssl_warning(url_to_test):
    """Make request and get reponse/handle any exceptions."""
    # Some domains(google.com) don't redirect to https if the user agent is not present
    headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) \
    Chrome/48.0.2564.103 Safari/537.36'}
    response = requests.get(url_to_test, headers=headers, verify=False, timeout=30)
    return response


def append_protocol(url_to_test):
    """Add protocol name to create a valid url."""
    url_to_test = url_to_test.replace("https://", "http://")
    if url_to_test.startswith('http://'):
        # Url starts with protocol: No need to append protocol
        pass
    else:
        url_to_test = "http://" + str(url_to_test)
    return url_to_test


def check_if_ssl_redirect_exists(url_to_test):
    """Take in a url and test if http redirects to https."""
    try:
        response = get_response_supress_ssl_warning(url_to_test)
        if response.url.startswith('https://'):
            DICT_FOR_RESULTS[INPUT_URL]['HTTP redirects to HTTPS'] = "Passed"
            print colored("TEST PASSED: http redirects to https", "green")
        else:
            DICT_FOR_RESULTS[INPUT_URL]['HTTP redirects to HTTPS'] = "Failed"
            print colored("TEST FAILED: http doesn't redirect to https", "red")
    except Exception as exception:
        print "Error occured when making a request to " + str(url_to_test) + "\nExiting now"
        print "Error: " + str(exception.__doc__)
        print "Details: " + str(exception.message)
        DICT_FOR_RESULTS[INPUT_URL]['HTTP redirects to HTTPS'] = ["Failed", "Error"]


def check_if_ssl_exists(url_to_test):
    """Check if the page exists over SSL."""
    try:
        ssl_url = url_to_test.replace("http://", "https://")
        ssl_r = get_response_supress_ssl_warning(ssl_url)
        if ssl_r.url.startswith('https://'):
            DICT_FOR_RESULTS[INPUT_URL]['Available over SSL'] = "Passed"
            print colored("TEST PASSED: Resource available over https", "green")
        else:
            print colored("TEST FAILED: Resource not available over https", "red")
            DICT_FOR_RESULTS[INPUT_URL]['Available over SSL'] = "Failed"
    except Exception as exception:
        print "Error occured when testing for https existance " + str(url_to_test)
        print colored("TEST FAILED: http doesn't redirect to https", "red")
        DICT_FOR_RESULTS[INPUT_URL]['Available over SSL'] = ["Failed", "Error"]
        print "Error: " + str(exception.__doc__)
        print "Details: " + str(exception.message)


def ssl_error_test(url_to_test):
    """Test for SSL errors."""
    try:
        ssl_url = url_to_test.replace("http://", "https://")
        get_response_ssl_error_exception(ssl_url)
    except Exception as exception:
        if exception.__doc__ == "An SSL error occurred.":
            DICT_FOR_RESULTS[INPUT_URL]['SSL errors'] = "Passed"
            print colored("SSL Error: " + str(exception.message), "red")
        else:
            print "Error occured when making a request to " + str(url_to_test) + "\nExiting now"
            print "Error: " + str(exception.__doc__)
            print "Details: " + str(exception.message)
            DICT_FOR_RESULTS[INPUT_URL]['SSL errors'] = "Failed"


def check_hsts_header(url_to_test):
    """Check if response contains HSTS header."""
    try:
        response = get_response_supress_ssl_warning(url_to_test)
        if 'strict-transport-security' in response.headers:
            DICT_FOR_RESULTS[INPUT_URL]['HSTS exists'] = True
            print colored("TEST PASSED: HSTS header exists", "green")
            if 'includeSubDomains' not in response.headers.get('strict-transport-security'):
                DICT_FOR_RESULTS[INPUT_URL]['HSTS configuration'] = "Missing includeSubDomains"
                print colored("TEST FAILED: HSTS doesn't include subdomains", "yellow")
            if int(filter(str.isdigit, response.headers.get('strict-transport-security'))) < 31536000:
                DICT_FOR_RESULTS[INPUT_URL]['HSTS configuration'] = "Age less than 12 months"
                print colored("TEST FAILED: Max-age is less than one year", "yellow")
            if 'includeSubDomains' not in response.headers.get('strict-transport-security') and int(filter(str.isdigit, response.headers.get('strict-transport-security'))) < 31536000:
                DICT_FOR_RESULTS[INPUT_URL]['HSTS configuration'] = "Missing includeSubdomains and Age less than 12 months"
            elif 'includeSubDomains' in response.headers.get('strict-transport-security') and int(filter(str.isdigit, response.headers.get('strict-transport-security'))) >= 31536000:
                DICT_FOR_RESULTS[INPUT_URL]['HSTS configuration'] = "Passed - Includes subdomains and max age at least 1 year"
                print colored("TEST PASSED: HSTS configured with max-age >= 12 months and include subdomains", "green")
        else:
            DICT_FOR_RESULTS[INPUT_URL]['HSTS exists'] = False
            print colored("TEST FAILED: HSTS header doesn't exist", "red")
            DICT_FOR_RESULTS[INPUT_URL]['HSTS configuration'] = "Failed"
            print colored("TEST FAILED: HSTS header doesn't exist so not configured properly", "red")
    except Exception as exception:
        print "Error: " + str(exception.__doc__)
        print "Details: " + str(exception.message)
        DICT_FOR_RESULTS[INPUT_URL]['HSTS configuration'] = "Error"


def check_cors_header(url_to_test):
    """Input response and check cors header."""
    try:
        response = get_response_supress_ssl_warning(url_to_test)
        if "Access-Control-Allow-Origin" in response.headers:
            # print "CORS exists"
            if response.headers.get("Access-Control-Allow-Origin") == "*":
                # print "Overly permissive CORS"
                print colored("TEST FAILED - Access-Control-Allow-Origin set to *", "red")
                DICT_FOR_RESULTS[INPUT_URL]['Access-Control-Allow-Origin'] = response.headers.get("Access-Control-Allow-Origin")
            else:
                print colored("TEST PASSED - Access-Control-Allow-Origin is not set to *", "green")
                DICT_FOR_RESULTS[INPUT_URL]['Access-Control-Allow-Origin'] = response.headers.get("Access-Control-Allow-Origin")
        else:
            print colored("Access-Control-Allow-Origin doesn't exist", "green")
            DICT_FOR_RESULTS[INPUT_URL]['Access-Control-Allow-Origin'] = "Not present"
    except Exception as exception:
        print "Error: " + str(exception.__doc__)
        print "Details: " + str(exception.message)
        DICT_FOR_RESULTS[INPUT_URL]['Access-Control-Allow-Origin'] = "Error"


def check_x_frame_options(url_to_test):
    """Input response and check x-frame-options header."""
    try:
        response = get_response_supress_ssl_warning(url_to_test)
        if "x-frame-options" in response.headers:
            # print "CORS exists"
            if response.headers.get("x-frame-options") == "DENY" or "SAMEORIGIN":
                # print "Overly permissive CORS"
                print colored("TEST PASSED - x-frame-options set to " + str(response.headers.get("x-frame-options")), "green")
                DICT_FOR_RESULTS[INPUT_URL]['x-frame-options'] = response.headers.get("x-frame-options")
            else:
                print colored("TEST PASSED - x-frame-options set to " + str(response.headers.get("x-frame-options")), "yellow")
                DICT_FOR_RESULTS[INPUT_URL]['x-frame-options'] = response.headers.get("x-frame-options")
        else:
            print colored("TEST FAILED - x-frame-options doesn't exist", "red")
            DICT_FOR_RESULTS[INPUT_URL]['x-frame-options'] = "Failed"
    except Exception as exception:
        print "Error: " + str(exception.__doc__)
        print "Details: " + str(exception.message)
        DICT_FOR_RESULTS[INPUT_URL]['x-frame-options'] = "Error"


def check_x_content_type_options(url_to_test):
    """Input response and check x-frame-options header."""
    try:
        response = get_response_supress_ssl_warning(url_to_test)
        if "x-frame-options" in response.headers:
            # print "CORS exists"
            if response.headers.get("x-content-type-options") == "nosniff":
                # print "Overly permissive CORS"
                print colored("TEST PASSED - x-content-type-options set to " + str(response.headers.get("x-content-type-options")), "green")
                DICT_FOR_RESULTS[INPUT_URL]['x-content-type-options'] = response.headers.get("x-content-type-options")
            else:
                print colored("TEST FAILED - x-content-type-options set to " + str(response.headers.get("x-content-type-options")), "yellow")
                DICT_FOR_RESULTS[INPUT_URL]['x-content-type-options'] = response.headers.get("x-content-type-options")
        else:
            print colored("TEST FAILED - x-content-type-options doesn't exist", "red")
            DICT_FOR_RESULTS[INPUT_URL]['x-content-type-options'] = "Failed"
    except Exception as exception:
        print "Error: " + str(exception.__doc__)
        print "Details: " + str(exception.message)
        DICT_FOR_RESULTS[INPUT_URL]['x-content-type-options'] = "Error"


def check_x_xss_protection(url_to_test):
    """Input response and check x-xss-protection header."""
    try:
        response = get_response_supress_ssl_warning(url_to_test)
        if "x-xss-protection" in response.headers:
            # print "CORS exists"
            if response.headers.get("x-xss-protection") == "1; mode=block":
                # print "Overly permissive CORS"
                print colored("TEST PASSED - x-xss-protection set to " + str(response.headers.get("x-xss-protection")), "green")
                DICT_FOR_RESULTS[INPUT_URL]['x-xss-protection'] = response.headers.get("x-xss-protection")
            else:
                print colored("TEST FAILED - x-xss-protection set to " + str(response.headers.get("x-xss-protection")), "yellow")
                DICT_FOR_RESULTS[INPUT_URL]['x-xss-protection'] = response.headers.get("x-xss-protection")
        else:
            print colored("TEST FAILED - x-xss-protection doesn't exist", "red")
            DICT_FOR_RESULTS[INPUT_URL]['x-xss-protection'] = "Failed"
    except Exception as exception:
        print "Error: " + str(exception.__doc__)
        print "Details: " + str(exception.message)
        DICT_FOR_RESULTS[INPUT_URL]['x-xss-protection'] = "Error"


def test_url(url_to_test):
    """The function to tests argument provided to script."""
    url_to_test = url_to_test
    url_to_test_protocol = append_protocol(url_to_test)
    if check_if_valid_url(url_to_test_protocol):
        check_if_ssl_redirect_exists(url_to_test_protocol)
        check_if_ssl_exists(url_to_test_protocol)
        ssl_error_test(url_to_test_protocol)
        check_hsts_header(url_to_test_protocol)
        check_cors_header(url_to_test_protocol)
        check_x_frame_options(url_to_test_protocol)
        check_x_content_type_options(url_to_test_protocol)
        check_x_xss_protection(url_to_test_protocol)
        json_parsed_full_response = result_from_cache(url_to_test)
        if json_parsed_full_response:
            # Uncomment the next line to see the entire response from SSL labs
            # print_json_parsed_response(json_parsed_full_response)
            DICT_COMPLETE_RESPONSE[INPUT_URL] = {}
            DICT_COMPLETE_RESPONSE[INPUT_URL]['Result'] = json_parsed_full_response
            get_ssl_labs_grade(json_parsed_full_response)
            ios_ats_test(json_parsed_full_response)

INPUT_FILE, INPUT_URL, OUTPUT_FILE = get_cl_arguments()
if INPUT_URL:
    DICT_FOR_RESULTS[INPUT_URL] = {}
    test_url(INPUT_URL)
if INPUT_FILE:
    INPUT_LIST = read_file(INPUT_FILE)
    for N in INPUT_LIST:
        # print N
        INPUT_URL = N
        DICT_FOR_RESULTS[INPUT_URL] = {}
        test_url(INPUT_URL)

pprint(DICT_FOR_RESULTS)
# pprint(DICT_COMPLETE_RESPONSE)
