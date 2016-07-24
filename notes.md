# Notes

Starting point was this quickstart tutorial <https://docs.docker.com/compose/django/>

This initialized the project

    $ docker-compose run --rm web django-admin.py startproject mysite .
    $ vim mysite/settings.py

Running the initial migration

    $ docker-compose run --rm web python manage.py migrate

To start a new app

    $ docker-compose run --rm web python manage.py startapp <app_name>

To bring up the containers:

    $ docker-compose up -d db
    $ docker-compose up -d web

To check the logs:

    $ docker-compose logs db
    $ docker-compose logs web

To stop (all) the containers:

    $ docker-compose stop

# Links
* <https://docs.docker.com/compose/django/>
* <https://docs.djangoproject.com/en/1.9/intro/tutorial01/>
