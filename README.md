# LHFG
This tool will run some basic tests on a url that are easily automatable. More tests will be added each week for the next few weeks  
Initial upload will only have SSL tests
This now has some additional headers and CORS policy check. See Tests section of this doc for complete list  
  
Checks for CSP, checks on cookie attributes and other security checks will be added over the next few weeks
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
* Check header value x-xss-protection: 1; mode=block
* Check header value x-content-type-options: nosniff
* Check header vale x-frame-options: DENY or SAMEORIGIN
* Check header Access-Control-Allow-Origin: *  

More info about headers <https://www.owasp.org/index.php/List_of_useful_HTTP_headers>  

More info about CORS <http://www.html5rocks.com/en/tutorials/cors/>

## Thanks to SSL labs
SSL labs grade, HSTS checks and Apple ATS check use SSL labs API
<https://www.ssllabs.com/projects/ssllabs-apis/index.html>
