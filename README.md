
[![](https://github.com/eoinoconnell04/final2/workflows/tests/badge.svg)](https://github.com/eoinoconnell04/final2/actions?query=workflow%3Atests)

# Instagram Text Stack

## Overview

In this project, I followed directions from https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/ to create a web service where you can upload images and files into a server. This project uses Flask, Docker, Postgres, Gunicorn, Nginx, in order to create server that is based on Instagram's tech stack. To access the server, I use portforwarding to connect the web service from the lambda server to firefox, where I can access it at the url http://localhost:8080/upload. Once the file has been uploaded, you can view the file at the url http://localhost:8080/media/file_name, where file_name is the name of the file that you uploaded. Note, this site can only be accessed on the same machine that has the portforwarding setup.

Here is an example of uploading an image on the website, and then accessing it within firefox.
<img src=uploading_image.gif />

## How to use the web service

In order to run the service on your machine, you start by forking this repository, and creating the necesary environment files. The three files that you need to create are `.end.dev`, `.env.prod`, and `.env.prod.db`. These files store all of the production credentials, and need to be kept private.
For `.end.dev`, you need to fill out all the following file with your credentials:

```
FLASK_APP=project/__init__.py
FLASK_DEBUG=1
DATABASE_URL=
SQL_HOST=db
SQL_PORT=5432
DATABASE=postgres
APP_FOLDER=/usr/src/app
```
Then `.env.prod`:
```
FLASK_APP=project/__init__.py
FLASK_DEBUG=0
DATABASE_URL=
SQL_HOST=db
SQL_PORT=5432
DATABASE=postgres
APP_FOLDER=/home/app/web
```
Then, `.env.prod.db`
```
POSTGRES_USER= 
POSTGRES_PASSWORD=
POSTGRES_DB=
```

## Development testing

To test the web service in development, we can run the container from the project's root directory with:
```
$ docker-compose up -d --build
```
Now you can create the database:
```
$ docker-compose exec web python manage.py create_db
```
Now, you can test the web page at http://localhost:9876/, where you should see a hello world readout. If this works as expected, we can bring back down this container with:
```
$ docker-compose down -v
```

## Final Production

Now, you can build the production contianer from the root directly of the project with:
```
$ docker-compose -f docker-compose.prod.yml up -d --build
```

Now you can create the database:
```
$ docker-compose -f docker-compose.prod.yml exec web python manage.py create_db
```
Now that the database is running, you can upload files at the url http://localhost:1337/upload, and then access these files at http://localhost:1337/media/file_name.
