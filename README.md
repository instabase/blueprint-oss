# Blueprint

Blueprint is a declarative extraction language for semi-structured documents.

# Setup

Start by cloning this repo to your machine.

## Python environment

### `venv`

You will need to install several Python packages. It is recommended that you
do this in a Python virtual environment, created using the Python `venv` module.
If you know what that means and how to do it, you can skip the rest of this
section.

If not, your choices are:

- Learn about `venv`: <https://docs.python.org/3/library/venv.html>
- Or, execute all of the commands below without creating/activating a virtual
  environment. The required packages will be installed globally on your machine
  (or globally to your user account on your machine). This isn't necessarily a
  problem, but a virtual environment keeps things tidy.
- Or, blindly follow the instructions in this paragraph. From the root of this
  repo, execute `python3 -m venv .venv` to create a virtual environment in a
  subdirectory called `.venv`, then execute `. .venv/bin/activate` to activate
  the virtual environment. Do this second step (the activate step) for every
  terminal you use to interact with the repo (starting the Studio server, etc.).

### `PYTHONPATH`

Add `path/to/blueprint-oss/blueprint/py` and `path/to/blueprint-oss/server/py`
to your `PYTHONPATH`. In most shells (Bash/Zsh), this can be accomplished by
running:

```
export PYTHONPATH="${PYTHONPATH}:path/to/blueprint-oss/blueprint/py:path/to/blueprint-oss/server/py"
```

For how to make this happen every time you start a new terminal, see:
<https://stackoverflow.com/questions/3402168/permanently-add-a-directory-to-pythonpath>

## Requirements

Install the Python requirements (ideally from within your `venv`) by running:

```
pip3 install -r python_requirements.txt
```

## JavaScript environment

If you are just using Blueprint's CLI, you can skip this section.

To run Studio, you will need to have Node/`npm` installed. There is probably
some minimum version but I'm not sure what it is. These instructions have been
tested using Node v17.0.1.

These instructions use `npm`, but `yarn` should also work.

## Requirements for Studio

Install Studio's JavaScript requirements (this will happen locally to the repo
automatically, and will not touch the rest of your machine):

```
cd studio
npm install
```

# Running Blueprint

## CLI

Blueprint provides a command-line interface. To run on a sample paystub:

```
cd examples/paystubs
python3 paystubs.py run_model -v -g ocr/*
```

To generate OCR for your own document samples, see:
<https://cloud.google.com/vision/docs/drag-and-drop>

# Running Studio

Studio is an interactive GUI application for inspecting document samples and
creating, running, testing, and debugging Blueprint extraction programs/models.

To use Studio, you will need to start a server hosting the frontend, and a
server hosting the backend.

## Frontend

The Studio frontend is a single-page web application written in
TypeScript/React. To start the server:

```
cd studio
npm start
```

## Backend

The Studio backend is a thin wrapper around the Blueprint Python module, which
allows the Studio frontend to execute Blueprint models and display the results.
To start the backend, run:

```
python3 -m bp_server
```

During development, it can be useful to turn on auto-reloading for the backend
server. This can be done by launching it like so:

```
FLASK_ENV=development python3 -m bp_server
```

## Example usage

Once you have started both the frontend and backend servers, open a browser to
`http://localhost:3000`. You should see the Studio welcome screen.

Click on the instructions button and read the instructions carefully. You can
make a copy of the `examples/paystubs` directory and use the copy as your
project directory -- then you should be able to view sample paystubs in the GUI.

Studio does not use Python-based Blueprint programs (for example, the reference
extraction program `paystubs.py`). You will need to make a new model.
