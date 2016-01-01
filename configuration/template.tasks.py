# this tasks file generated with vagrant_django
# requires 'project_slug' be defined

import os

from invoke import task, run
from invoke.exceptions import Failure

HOME_PATH = os.environ['HOME']
DJANGO_PATH = os.path.join(HOME_PATH, 'vagrant_django', '${project_slug}')
CONF_PATH = os.path.join(HOME_PATH, 'vagrant_django', 'configuration')
UWSGI_LOG_PATH = os.path.join(HOME_PATH, 'logs', 'uwsgi.log')
UWSGI_SH_PATH = os.path.join(HOME_PATH, 'uwsgi.sh')
UWSGI_PID_PATH = os.path.join(HOME_PATH, 'uwsgi.pid')

def multiple(*args):
    return " && ".join(args)

@task
def home(command, *args, **kwargs):
    """ Run a command from the base ${project_slug} directory """
    return run(multiple("cd {}".format(DJANGO_PATH), command), *args, **kwargs)

@task
def lint():
    """ Run the PEP8 and Pyflakes linters """
    return home(multiple("pep8 */*.py --ignore=\"E128,E501,E402\"",
                       "pyflakes */*.py"))

@task
def dj(command, *args, **kwargs):
    """ Run a django manage.py command """
    return home("python3 manage.py {}".format(command), *args, **kwargs)

@task()
def runserver():
    """ Run a django development server """
    print("Running server on localhost:8080 (Vagrant Host:18080)")
    return dj("runserver 0:8080", pty=True)

@task
def migrate():
    """ Prep the database """
    return dj("migrate")

@task()
def testdata():
    """ Generate test data for the site. """
    dj("testdata")

@task()
def celery():
    """ Activate celery worker for testing. """
    print("Activating celery worker for testing.")
    return dev("celery --app=threepanel worker -l info")

@task()
def beat():
    """ Run a celery beat for testing. """
    print("Running a celery beat for testing.")
    return dev("celery --app=threepanel beat")

@task()
def clear():
    """ CLEAR DA CACHE """
    print("Clearing everything out of the redis cache.")
    dj("clear_cache")

@task()
def dump():
    """ Dump the Postgres DB to a file. """
    print("Dumping DB")
    run("dos2unix {}/backup_postgres.sh".format(CONF_PATH))
    run("bash {}/backup_postgres.sh".format(CONF_PATH))

@task()
def restore(filename):
    """ Restore the Postgres DB from a file. """
    print("Dumping DB")
    dump()
    print("Destrying DB")
    run("dos2unix {}/reset_postgres.sh".format(CONF_PATH))
    run("bash {}/reset_postgres.sh".format(CONF_PATH))
    print("Restoring DB from file: {}".format(filename))
    run("dos2unix {}/rebuild_postgres.sh".format(CONF_PATH))
    run("bash {}/rebuild_postgres.sh {}".format(CONF_PATH, filename), echo=True)

@task()
def clear():
    """ Destroy and recreate the database """
    print("Resetting db")
    dump()
    run("dos2unix {}/reset_postgres.sh".format(CONF_PATH))
    run("bash {}/reset_postgres.sh".format(CONF_PATH))
    dj("makemigrations")
    dj("migrate --noinput")
    #dj("testdata")

@task
def uwsgi():
    print("writing logs to {}".format(UWSGI_LOG_PATH))
    print("writing pidfile to {}".format(UWSGI_PID_PATH))
    run("bash {}/uwsgi.sh".format(HOME_PATH))

@task
def kill_uwsgi():
    if os.path.exists("{}/uwsgi.pid".format(HOME_PATH)):
        print("Killing UWSGI...")
        run("kill `cat {}/uwsgi.pid`".format(HOME_PATH), pty=True)
        run("sleep 1")
        run("ps aux | grep uwsgi")
        print("UWSGI Dead...")
    else:
        print("UWSGI not running!")

@task
def prod_restart():
    """ Restart all of the services that make up ${project_slug} """
    prod_stop()
    prod_start()

@task
def prod_start():
    """ Start all of the services that make up Threepanel """
    uwsgi()
    run("sudo service nginx start")
    run("sudo service redis-server start")

@task
def prod_stop():
    """ Stop all of the services that make up Threepanel """
    kill_uwsgi()
    print("Killing Nginx...")
    run("sudo service nginx stop")
    print("Killing Redis...")
    run("sudo service redis-server stop")
