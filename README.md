<div align="center">
    <br>
    <img src="./ui/src/components/sidebar/pawlsLogo.png" width="400"/>

    PDF Annotations with Labels and Structure is software that makes it easy
    to collect a series of annotations associated with a PDF document. It was written
    specifically for annotating academic papers within the [Semantic Scholar](https://www.semanticscholar.org) corpus, but can be used with any collection of PDF documents.

</div>

### Getting Started

In order to run a local environment, you'll need to use the [PAWLS CLI](cli/readme.md) to download the PDFs and metadata you want to serve. The PDFs should be put in `skiff_files/apps/pawls`.

For instance, you can run this command to download the specified PDF:

```bash
  # Fetches pdfs from semantic scholar's S3 buckets.
  python scripts/ai2-internal/fetch_pdfs.py skiff_files/apps/pawls/papers 34f25a8704614163c4095b3ee2fc969b60de4698 3febb2bed8865945e7fddc99efd791887bb7e14f 553c58a05e25f794d24e8db8c2b8fdb9603e6a29
  # ensure that the papers are pre-processed with grobid so that they have token information.
  pawls preprocess grobid skiff_files/apps/pawls/papers
  # Assign the development user to all the papers we've downloaded.
  pawls assign skiff_files/apps/pawls/papers development_user --all --name-file skiff_files/apps/pawls/papers/name_mapping.json
```

and then open up the UI locally by running `docker-compose up`.

### Authentication and Authorization

*Authentication* is simply checking that users are who they say they are. Whether
or not these users' requests are allowed (e.g., to view a PDFs) is considerd
*authorization*. See more about this distinction at [Skiff
Login](https://skiff.allenai.org/login.html).

#### Authentication

All requests must be authenticated.

* The production deployment of PAWLS uses [Skiff
  Login](https://skiff.allenai.org/login.html) to authenticate requests. New
  users are bounced to a Google login workflow, and redirected back to the site
  if they authenticate with Google. Authenticated requests carry an HTTP header
  that identifies the user.
* For local development, there is no login workflow. Instead, all requests are
  supplemented with a hard-coded authentication header in
  [proxy/local.conf](proxy/local.conf) specifying that the user is
  `development_user@example.com`.

Look at the function `get_user_from_header` in [main.py](api/main.py) for
details.

#### Authorization

Authorization is enforced by the PAWLS app. A file of allowed user email
addresses is consulted on every request.

* In production, this file is sourced from [the secret named
  "users"](http://marina.apps.allenai.org/a/pawls/s/users) in Marina, which is
  projected to `/users/allowed.txt` in the container.
* For local development, this file is sourced from
  [allowed_users_local_development.txt](api/config/allowed_users_local_development.txt),
  and also projected to `/users/allowed.txt` in the Docker container.

The format of the file is simply a list of allowed email addresses.

There's a special case when an allowed email address in this file starts with
"@", meaning all users in that domain are allowed. That is, an entry
"@allenai.org" will grant access to all AI2 people.

Look at the function `user_is_allowed` in [main.py](api/main.py) for details.

### Python Development

The Python service and Python cli are formatted using `black` and `flake8`. Currently this is run in a local environment
using the app's `requirements.txt`. To run the linters:

```
black api/
flake8 api/
```


## Prerequisites

Make sure that you have the latest version of [Docker 🐳](https://www.docker.com/get-started)
installed on your local machine.

## Getting Started

Start by opening `skiff.json` and updating the `appName`, `contact` and
`team` fields:

* The `appName` field should be a short, unique and url-safe identifier for
  your application. This value determines the url of your application, which
  will be `${appName}.apps.allenai.org`.
* The `contact` field should be the `@allenai.org` email address that is
  responsible for the demo. Don't include the `@allenai.org` portion,
  just the prefix.
* The `team` field is the name of the team at AI2 that's responsible for
  the demo.

After commiting and pushing these changes make sure to submit a
[request to be onboarded](https://github.com/allenai/skiff/issues/new/choose).

To start a version of the application locally for development purposes, run
this command:

```
~ docker-compose up --build
```

This process launches 3 services, the `ui`, `api` and a `proxy` responsible
for forwarding traffic to the appropriate services. You'll see output
from each.

It might take a minute or two for your application to start, particularly
if it's the first time you've executed this command. Be patience and wait
for a clear message indicating that all of the required services have
started up.

As you make changes the running application will be automatically updated.
Simply refresh your browser to see them.

Sometimes one portion of your application will crash due to errors in the code.
When this occurs resolve the related issue and re-run `docker-compose up --build`
to start things back up.

## Installing Third Party Packages

You'll likely want to install third party packages at some point. To do so
follow the steps described below.

### Python Dependencies

To add new dependencies to the Python portion of the project, follow these steps:

1. Make sure your local environment is running (i.e. you've ran `docker-compose up`).
2. Start a shell session in the server container:
    ```
    ~ ./bin/sh api
    ```
3. Install the dependency in question:
    ```
    ~ python -m pip install <dependency>
    ```
4. Update the dependency manifest:
    ```
    ~ python -m pip freeze -l > requirements.txt
    ```
5. Exit the container:
    ```
    ~ exit
    ```

Remember to commit and push the `requirements.txt` file to apply your changes.

### UI Dependencies

To add new dependencies to the UI, follow these steps:

1. Make sure your local environment is running (i.e. you've ran `docker-compose up`).
2. Start a shell session in the ui container:
    ```
    ~./bin/sh ui
    ```
3. Install the dependency in question:
    ```
    ~ yarn add <dependency>
    ```
4. Exit the container:
    ```
    ~ exit
    ```

Remember to commit and push both the `yarn.lock` and `package.json` files
to apply your changes.

## Deploying

Your changes will be deployed automatically after they're pushed to branch `master`.
For more information about your application visit the [Skiff Marina](https://marina.apps.allenai.org).

If you'd like to deploy a temporary, ad-hoc environment to preview your changes,
view [this documentation](https://github.com/allenai/skiff/blob/master/doc/CreatingEnvironments.md).

## Development Tips and Tricks

The skiff template contains some features which are ideal for a robust web application, but might be un-intuitive for researchers.
Below are some small technical points that might help you if you are making substantial changes to the skiff template.

* Skiff uses `sonar` to check that all parts of the application (frontend, backend) are up and running before serving requests.
To do this, it checks that your api returns 2XX codes from its root url - if you change the server, you'll need to make sure to add
code which returns a 2XX response from your server.

* To ease development/deployment differences, skiff uses a proxy to route different urls to different containers in your application.
The TL;DR of this is the following:

| External URL           |    Internal URL    | Container |
|------------------------|:------------------:|:---------:|
| `localhost:8080/*`     | `localhost:3000/*` |    `ui`   |
| `localhost:8080/api/*` | `localhost:8000/*` |   `api`   |

So, in your web application, you would make a request, e.g `axios.get("/api/route", data)`, which the server recieves at `localhost:8000/route`.
This makes it easy to develop without worrying about where apis will be hosted in production vs development, and also allows for things like
rate limiting. The configuration for the proxy lives [here](https://github.com/allenai/skiff-template/blob/master/proxy/local.conf) for development and [here](https://github.com/allenai/skiff-template/blob/master/proxy/prod.conf) for production.

For example, if you wanted to expose the `docs` route `localhost:8000/docs` from your `api` container to users of your app in production, you would add this to `prod.conf`:

```
location /docs/ {
    limit_req zone=api;
    proxy_pass http://api:8000/;
}
```
* [.skiff/webapp.jsonnet](https://github.com/allenai/skiff-template/blob/master/.skiff/webapp.jsonnet) contains lots of deployment details which
you might wish to change/configure, particularly if your Docker images are built differently from the default ones in `skiff-template` (for instance, if they take different arguments to start the server).



## Metrics and Logs

You can find links to the metrics and log entries related to your application
by visiting the [Marina](https://marina.apps.allenai.org).

## Helpful Links

Here's a list of resources that might be helpful as you get started:

* [Skiff User Guide](https://github.com/allenai/skiff/blob/master/doc/UserGuide.md)
* [TypeScript in 5 minutes](https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html)
* [ReactJS Tutorial](https://reactjs.org/tutorial/tutorial.html)
* [Flask Documentation](http://flask.pocoo.org/docs/1.0/)
* [Varnish](https://github.com/allenai/varnish)

## Getting Help

If you're stuck don't hesitate to reach out:

* Sending an email to [reviz@allenai.org](mailto:reviz@allenai.org)
* Joining the `#skiff-users` slack channel
* Opening a [Github Issue](https://github.com/allenai/skiff/issues/new/choose)

We're eager to improve `skiff` and need your feedback to do so!

Smooth sailing ⛵️!
