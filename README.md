# LHFG
This tool will run some basic tests on a url that are easily automatable. More tests will be added each week for the next few weeks  
Initial upload will only have SSL tests  
Checks for CSP, checks on cookie attributes and other security headers will be added over the next few weeks
## Usage
* Open terminal
* Go to the directory where LHFG.py is
* Run the tests on single url - "python LHFG.py -u <url to test>"
* To run for multiple urls - "python LHFG.py -i <input_file>"
* Input file should contain newline seperated urls

## Tests
* Check if a url is available over https
* Check if http request to url redirects to https
* Get SSL labs grade - fail message if grade worse than A[A+, A, A-]
* Check if HSTS header is set
* Check if HSTS has max-age > 12 months and includeSubDomains
* Check if the domain is compatible with Apple ATS

## Thanks to SSL labs
SSL labs grade, HSTS checks and Apple ATS check use SSL labs API
<https://www.ssllabs.com/projects/ssllabs-apis/index.html>
