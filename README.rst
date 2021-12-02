Proof of Concept WSGI Demo
==========================

Demo WSGI framework. The code has only standard python module dependencies and
so it can be used without setup. It should work on linux on python 3.6 or
higher. To test user login use the manage.py
file: `python manage.py user add <username password>`

This code is not meant to be
used in production, rather the intention is to explore some
architectural and coding principles. It uses no dependencies
except for the templating system, which is a one file template
module taken from
here: https://www.simple-is-better.org/template/pyratemp.html.

Other than that only standard python modules are used. To
test this code no istallation and no virtual environment is
required: it is enough to run ``python wsgy.py`` on
command line. The code is written for Python 3.6 or above.
       
Some of the features highlighted in this project.

- The framework is written to be WSGI compliant and can be served by any server supporting this protocol.
- A website created using this approach can be grafted onto another site with minimal change.
- Client side password encryption for non HTTPS connection.
- View access control.
