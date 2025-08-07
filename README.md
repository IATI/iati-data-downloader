# IATI Data Downloader

## Summary

| Product          | IATI Data Downloader |
| ---------------- | ---------------------------------
| Description      | A Python Azure Functions app which recieves requests to download datasets from the IATI Bulk Data Service, attempts to download them, if successful, uploads IATI XML files to the IATI cache (Azure blob storage) both as XML and as individual ZIP files, and then sends the results back to the Bulk Data Service. |
| Website          | n/a  |
| Related          | [IATI Message Queue Service](https://github.com/IATI/iati-message-queue-service), [IATI Bulk Data Service](https://github.com/IATI/bulk-data-service) |
| Documentation    | Rest of `README` |
| Technical Issues | See https://github.com/IATI/iati-data-downloader/issues |
| Support          | https://iatistandard.org/en/guidance/get-support/  |

## Description

The Data Downloader is part of the IATI Secretariat's internal data pipeline. It
receives messages from the Bulk Data Service via the IATI Message Queue Service
and after attempting download and upload to the IATI cache it sends the results back to the Bulk Data Service.

## High-level requirements

- Python 3.13
  - (This is specified in .python-version and pyproject.toml)
- Azure storage account with blob storage enabled
- IATI Message Queue Service

## Running the app locally

### First-time setup

#### 1. Setup and activate a Python virtual environment.

```
python -m venv .ve
source .ve/bin/activate
```

_Note: if you don't use `pyenv`, you may need to run `python3.13 -m venv .ve`_

#### 2. Install the dependencies

```
pip install -r requirements.txt
```

#### 3. Setup `local-settings.json`

The IATI Data Downloader is an Azure Functions app. It can be run locally using
'Azure Functions Core Tools', and when running that way it is configured using a
file called `local-settings.json`. To setup this file:

Copy `local.settings-example.json` to `local.settings.json` and fill in the
following three configuration values: `MQS_CONNECTION_STRING`,
`MQS_DOWNLOAD_REQUEST_QUEUE_NAME`, `MQS_DOWNLOAD_ATTEMPT_RESULT_TOPIC_NAME`.

These three values configure the Data Downloader's use of the IATI Message Queue
Service. The latter two are the queue and topic name and are prefilled in with
the name *prefix* - you'll need to change `FIXME` according to what instance
you're going to run against.

The `MQS_CONNECTION_STRING` should be filled in with the appropriate
authorisation string - if running locally against the dev instance, get the
string from the Azure Portal.

The app also requires access to an Azure blob storage setup. It can use
Azurite, the development Azure blob storage emulator, and the values needed to
connect to Azurite on the default ports are already in the example config
file.

### Run the app after initial setup

If running with Visual Studio code, you can press Ctrl-Shift-D and then F5 and
VS Code will start the Functions app and connect its debugger to the Python
interpreter.

If running from the command line, run with:

```bash
func host start
```

## Development on the app

### Code formatting and checking

The project is set up with various code linters and formatters. You can setup
your IDE to run them automatically on file save, or you can run them manually.
(Configuration files are included for VS Code).

To run these you need to install the extra development dependencies into the
Python virtual environment using the following:

```
pip install -r requirements-dev.txt
```

_**Note**: these linters are run as a CI job, so pushes and PRs will fail GitHub
checks if the formatters haven't been run or any of the linters generate
warnings._


#### isort

Import sorter `isort` is configured via `pyproject.toml` and can be run with:

```
isort .
```

#### black

Code formatter `black` is configured via `pyproject.toml` and can be run with:

```
black .
```

#### flake8

Flake8 is configured via `pyproject.toml`, and can be run with:

```
flake8 .
```

#### mypy

Type checker `mypy` is configured via `pyproject.toml`. It can be run with:

```
mypy
```

#### All at once

```
isort .; black .; flake8 .; mypy
```

### Adding new dependencies to main project

New dependencies need to be added to `pyproject.toml`.

After new dependencies have been added, `requirements.txt` should be regenerated
using:

```
pip-compile -o requirements.txt pyproject.toml
```

Include `--upgrade` if you want to upgrade the existing packages.

### Adding new dependencies to the development environment

New development dependencies need to be added to `pyproject.toml` in the `dev`
value of the `[project.optional-dependencies]` section.

After new dev dependencies have been added, `requirements-dev.txt` should be
regenerated using:

```
pip-compile --extra dev -o requirements-dev.txt pyproject.toml
```

Include `--upgrade` if you want to upgrade the existing packages.

### Automated tests

Requirements: docker compose

Unit and integration tests are written in `pytest`. The integration tests work
by running bits of the code against mock servers and emulators. There is a
docker compose setup which launches Azurite and a Mockoon server.

The Azurite is ephemeral and doesn't persist any data to disk.

The Mockoon server serves the artefacts in `tests/artefacts` on
`http://localhost:3005/data/` and the artefacts (datasets) in
`tests/artefacts/dataset-files` on `http://localhost:3005/datasets/` and lets
you request specific error codes at
`http://localhost:3005/error-response/HTTPSTATUSCODE`. (Note: you can't browse
the folders via the Mockoon server)

To run the tests, start this docker compose setup with:

```
cd tests/test-environment
docker compose up --remove-orphans
```

_**Note**: the `--remove-orphans` just helps keep things clean as you develop, and
alter the setup._

Once this is running, run the tests with:

```
pytest
```

This automated test environment is configured via the following files:

`tests/test-environment/.env`

`tests/test-environment/docker-compose.yml`

`tests/test-environment/mockoon-server-config.json`

If you need to edit the Mockoon setup, by far the easiest way is to use the
Mockoon GUI.

_**Note**: these tests are run as a CI job, so pushes and PRs will fail GitHub
checks if any of the tests are failing._

### Automatically running the automated tests

When you are developing you may want to have the tests run whenever you make changes. `pytest-watcher` is installed for this purpose and you can run it with the following command:

```bash
pytest-watcher .
```

## Provisioning and Deployment

### Initial Provisioning

Provisioning and Azure resource re-configuration is done with the IATI OpenTofu
setup. Instances can be created/renamed/deleted by making changes to the primary
`main.tf` file in the IATI deploy repo. Changes to the resource configuration
should be done by altering the 'data_downloader' module in the OpenTofu setup.

### Deployment - Versioning

The app version is set in `pyproject.toml`, and this is read by the app to use
in the `User-Agent` header. When making a new release, set the version here to
the appropriate value. Then, when releasing the app using the normal IATI Python
app deployment process, choose the tag name to match the version chosen.

### Deployment - Automated deployment via GitHub Actions

TODO

## Resources

[Reference docs for the Azure deployment YAML
file](https://learn.microsoft.com/en-us/azure/container-instances/container-instances-reference-yaml#schema)
(`azure-deployment/deploy.yml`).
