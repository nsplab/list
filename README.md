# list

Install Docker

    For Mac: https://docs.docker.com/docker-for-mac/
    For Windows: https://docs.docker.com/docker-for-windows/

Clone the repository and cd into the top-level directory containing the docker-compose.yml file.

Start the db container (daemonized using -d)

    $ docker-compose up -d db

Check the logs and verify the container is up:

    $ docker-compose logs db

Run the migration to create the tables in the database:

    $ docker-compose run --rm web python manage.py migrate

One-time action to the load some stored functions. First, connect to the database using psql.

    $ docker-compose run --rm db psql -d listdev -U devel -h db
    At the prompt, enter the password contained in mysite/settings.py.
    
    Now, you are in the psql client, and the prompt should indicate the listdev database.
    At the prompt, execute the following command to the load the stored functions:
    listdev=> \i /storedfunc.sql
    It should say CREATE FUNCTION as the output.
    Exit the psql client with the \q command.

Activate the web container (this runs the django development server)

    $ docker-compose up -d web

Vist the website at localhost:8081/lists/

Stop the containers:

    $ docker-compose stop

More information can be found by typing docker-compose -h.
