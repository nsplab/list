# Notes

Starting point was this quickstart tutorial <https://docs.docker.com/compose/django/>

This initialized the project

    $ docker-compose run --rm web django-admin.py startproject mysite .
    $ vim mysite/settings.py

Running the initial migration

    $ docker-compose run --rm web python manage.py migrate

Starting a new app

    $ docker-compose run --rm web python manage.py startapp lists

To bring up the web container

    $ docker-compose up

# Links
* <https://docs.docker.com/compose/django/>
* <https://docs.djangoproject.com/en/1.9/intro/tutorial01/>
