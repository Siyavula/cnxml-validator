Siyavula cnxmlplus-validator
============================

This package provides the machinery to validate any cnxmlplus document, and the
subsequent conversion to either LaTeX or HTML. This is a low level library and
as such it is used elsewhere in wrapper applications (such as exercises server,
and the bookbuilder app).


# Installation
**WARNING** if the following doesn't work please create a github issue at
https://github.com/Siyavula/cnxml-validator

I may not have listed the prerequisites 100% completely.

You need (probably) the following packages installed on an Ubuntu >=12.04:

    libxml2
    libxml2-dev
    build-essentials
    python-setuptools

Run the following to install them:

    sudo apt-get install libxml2 libxml2-dev build-essentials python-setuptools


## Steps

Clone this repo, change into that folder, install the required python packages
and then install the validator system-wide.

    git clone https://github.com/Siyavula/cnxml-validator
    cd cnxml-validator
    sudo pip install -r requirements.txt
    sudo python setup.py install

Once this is done, you can check whether the installation worked:

    cnxmlplus-validate testdocuments/03-atomic-combinations.cnxmlplus

This should produce **no** output.


