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

In one terminal run this command, the web-service will start on port 5000

```bash
python minimailgun/api.py
```

To enable the service auto-reloading on change of code, set the environment variable `MINI_MAILGUN_DEBUG` to any value

```bash
export MINI_MAILGUN_DEBUG=1
```


Running Celery Worker Pool
--------------------------

In another terminal start celery by

```bash
celery worker -A minimailgun.tasks -l INFO
```

Running Unit tests
------------------

Run unit-test with this command

```bash
python setup.py test
```


REST API
========

Create a mail
--------------

POST a JSON payload to `/mail` route will create a mail

```bash
curl -X POST -H 'Content-Type:application/json' -H 'Accept:application/json' -d '{
  "from": "sender@sendingplace.com",
  "to": ["foo@example1.com", "foobar@somewhere.com", "foobaz@elsewhere.com"],
  "message": "To: Joe Black<foobaz@elsewehre.com>\r\nSubject: Hello World\r\nDate: Jan 01, 2020\r\nHello Joe,\r\nThis is a very important message from BabyGun.\r\n"
}' http://localhost:5000/mail
```

This will return a response something like:
```bash
{
    "_created_at": "Fri, 25 Sep 2015 05:42:01 GMT",
    "_id": "9d861b06-f608-4239-b3e9-4fe311ce6c05",
    "_recipients": {
        "foo@example1_com": {
            "email": "foo@example1.com",
            "status": "New",
            "updated": "Fri, 25 Sep 2015 05:42:01 GMT"
        },
        "foobar@somewhere_com": {
            "email": "foobar@somewhere.com",
            "status": "New",
            "updated": "Fri, 25 Sep 2015 05:42:01 GMT"
        },
        "foobaz@elsewhere_com": {
            "email": "foobaz@elsewhere.com",
            "status": "New",
            "updated": "Fri, 25 Sep 2015 05:42:01 GMT"
        }
    },
    "from": "sender@sendingplace.com",
    "message": "To: Joe Black<foobaz@elsewehre.com>\r\nSubject: Hello World\r\nDate: Jan 01, 2020\r\nHello Joe,\r\nThis is a very important message from BabyGun.\r\n",
    "to": [
        "foo@example1.com",
        "foobar@somewhere.com",
        "foobaz@elsewhere.com"
    ]
}
```

Get the status of message
-------------------------

GET Call

```bash
curl -X GET -H 'Accept:application/json' http://localhost:5000/mail/9d861b06-f608-4239-b3e9-4fe311ce6c05
```

Response
```bash
{
    "_created_at": "Fri, 25 Sep 2015 06:02:54 GMT",
    "_id": "9d861b06-f608-4239-b3e9-4fe311ce6c05",
    "_recipients": {
        "foo@example1_com": {
            "email": "foo@example1.com",
            "status": "Delivered",
            "updated": "Fri, 25 Sep 2015 06:02:56 GMT"
        },
        "foobar@somewhere_com": {
            "email": "foobar@somewhere.com",
            "status": "Fatal DNS Error. No Retry <class 'dns.resolver.NXDOMAIN'>",
            "updated": "Fri, 25 Sep 2015 06:02:56 GMT"
        },
        "foobaz@elsewhere_com": {
            "email": "foobaz@elsewhere.com",
            "status": "New",
            "updated": "Fri, 25 Sep 2015 06:02:56 GMT"
        },
    },
    "from": "sender@sendingplace.com",
    "message": "To: Joe Black<foobaz@elsewehre.com>\r\nSubject: Hello World\r\nDate: Jan 01, 2020\r\nHello Joe,\r\nThis is a very important message from BabyGun.\r\n",
    "to": [
        "foo@example1.com",
        "foobar@somewhere.com",
        "foobaz@elsewhere.com"
    ]
}
```
