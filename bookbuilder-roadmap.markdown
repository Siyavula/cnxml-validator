# Roadmap for bookbuilder
bookbuilder is an application that encapsulates the machinery contained in
XmlValidator and the associated spec\*.xml files. It is meant as a one-stop
tool for the validation of cnxmlplus files and the conversion from there to 
various output formats, including LaTeX, html for web, html for mobile and epub
3.


## End-goals for users

 Goal                                      | Status 
-------------------------------------------|--------
Validate book repo and give output         | Done
LaTeX output                               | Done
Minimal PDF manual layout                  | Not started
HTML web output                            | Not started
XHTML for Epub 3.0                         | Not started
HTML for mobile                            | Not started
Efficiency                                 | In progress
Documentation                              | In progress

## End-goals from code perspective

 Goal                                      | Status 
-------------------------------------------|--------
Code documentation                         | Comments and doc strings only
Tests                                      | Not started
Maintainability                            | Code is PEP8 compliant but overall documentation must be written to support future maintenance



## Next goals

### User goals

*   HTML output
*   Epub output (this relies on HTML output working correctly)


### Code goals

*   Automated tests
    * This will require some refactoring to get classes and methods untangled
