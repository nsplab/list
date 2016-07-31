# list


## Instructions For Windows

Install Docker

* <https://docs.docker.com/docker-for-windows/>

Clone the repository and cd into the top-level directory containing the docker-compose.win.yml file.

Start the db container (daemonized using -d)

    $ docker-compose -f docker-compose.win.yml up -d db

Check the logs and verify the container is up:

    $ docker-compose -f docker-compose.win.yml logs db

Edit your hosts file located at: ``C:\WINDOWS\system32\drivers\etc\hosts`` and add/edit the line pointing to localhost to include the hostname ``db`` like so:

	127.0.0.1 localhost db

Install PGAdmin3 <https://www.pgadmin.org/download/windows.php>

Add a new server and verify that you can connect to the listdev database at ``db:5432`` with the credentials listed in the docker-compose yml file.

Run the migration to create the tables in the database. This will not use Docker. You need to create a virtualenv with psycopg2 and django, and activate it.

    $ python manage.py migrate

One-time action to load some stored functions into the database

    $ docker exec -it list_db_1 /bin/bash

    Now you are inside the shell. Use the password in mysite/settings.py
    $ PGPASSWORD=(passwd) psql -U devel -h db listdev < /storedfunc.sql

Run the Django development server (in your virtualenv)

    $ python manage.py runserver 0.0.0.0:8081

Vist the website at <localhost:8081/listapp/>

Stop the database container:

    $ docker-compose stop


## Instructions For MacOS

Install Docker

* <https://docs.docker.com/docker-for-mac/>

Clone the repository and cd into the top-level directory containing the docker-compose.yml file.

Start the db container (daemonized using -d)

    $ docker-compose up -d db

Check the logs and verify the container is up:

    $ docker-compose logs db

Run the migration to create the tables in the database:

    $ docker-compose run --rm web python manage.py migrate

One-time action to load some stored functions. First, connect to the database using psql.

    $ docker-compose run --rm db psql -d listdev -U devel -h db
    At the prompt, enter the password contained in mysite/settings.py.
    
    Now, you are in the psql client, and the prompt should indicate the listdev database.
    At the prompt, execute the following command to the load the stored functions:
    listdev=> \i /storedfunc.sql
    It should say CREATE FUNCTION as the output.
    Exit the psql client with the \q command.

Activate the web container (this runs the django development server)

    $ docker-compose up -d web

Vist the website at <localhost:8081/listapp/>

Stop the containers:

    $ docker-compose stop

More information can be found by typing docker-compose -h.
