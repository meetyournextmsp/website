# Meet Your Next MSP Website 

## Live

https://meetyournextmsp.scot/

## Dev

To run a dev copy:

Create a Python Virtual Environment. We use Python 3.6 on the live server.

Install dependencies:

    pip install -r requirements.txt 

Download the latest event database from https://meetyournextmsp2021data.netlify.app/database.sqlite and save it in the directory.

Create a directory called `contribs`.

Notice the `postcodes.sqlite` file in the repository - you'll need it next.

Create a directory called `instance` in the root of the checked out code. Add a file called `config.py`. Its contents should be:

    DATABASE_POSTCODES="postcodes.sqlite"
    DATABASE="database-you-downloaded.sqlite"
    CONTRIBUTIONS_DIRECTORY = "contribs"

Edit the paths to be full paths to the relevant files or directories.

Run 

    FLASK_ENV=development  FLASK_APP=meetyournextmsp  python -m flask run

Go to http://localhost:5000/


