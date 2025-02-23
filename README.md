# Okapi Code Tutoring Platform

## Project structure
The project is called `code_tutors`.  It currently consists of a single app `tutorials`.
All the HTML Bootstrap templates are in the templates folder and all models and views to handle the models can be found in the views.py and models.py file respectively.
All tests created are placed in the Tests folder and the urls.py file manages switching.

## Installation instructions
To install the software and use it in your local development environment, you must first set up and activate a local development environment.  From the root of the project:

```
$ virtualenv venv
$ source venv/bin/activate
```

Install all required packages:

```
$ pip3 install -r requirements.txt
```

Migrate the database:

```
$ python3 manage.py migrate
```

Seed the development database with:

```
$ python3 manage.py seed
```

Run all tests with:
```
$ python3 manage.py test
```

## Sources
The packages used by this application are specified in `requirements.txt`

