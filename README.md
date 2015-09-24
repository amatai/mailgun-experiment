Mailgun-experiment
==================

This is just an experiment to see what it takes to build a project like Mailgun

Requirements
============
Few requirements before you can start running it:

- Python3.4
- A MongoDB installation, has been tested with local installation of MongoDB alone.


Local Dev Installation
======================

### Clone the repository
Clone this repository locally.

```bash
cd /path/where/you/dev
git clone git@github.com:amatai/mailgun-experiment.git
```

### Create a virtualenv

This assumes virtualenvwrapper is installed on your local dev box.

```bash
cd /path/where/you/cloned/mailgun-experiment
mkvirtualenv -p `which python3` -a `pwd` minimailgun
```

### Install and Run

#### Install and run MongoDB

Follow instructions from http://docs.mongodb.org/manual/installation/ to install MongoDB

Create a directory to let MongoDB save DB files and run MongoD

```bash
mkdir /path/to/mongodb/data
mongod --dbpath /path/to/mongodb/data
```

#### Virtualenv and Depdendencies
The virtualenv should be activated when the env is created. If you are coming back to work on it: `workon minimailgun` should activate it.

```bash
cd /path/to/project/dir
pip install -e .
```

#### Running the services

This experiment uses Flask for API and Celery for background tasks. These are run separately as two services. Hence, get two terminals
and activate the virtualenv in both of them.

Running the API
---------------

In one terminal run this command

```bash
python minimailgun/api.py
```

The web-service runs on port 5000


Running Celery Worker Pool
--------------------------

In another terminal start celery by

```bash
celery worker -A minimailgun.tasks -l INFO
```
