<div align="center">
    <img src="./ui/src/components/sidebar/pawlsLogo.png" width="400"/>

[Demo Server](https://pawls.apps.allenai.org) | [Video Tutorial](https://www.youtube.com/watch?v=TB4kzh2H9og) | [Paper](https://arxiv.org/pdf/2101.10281v1.pdf)
</div>

------------------------------------------------
  PDF Annotations with Labels and Structure is software that makes it easy
  to collect a series of annotations associated with a PDF document. It was written
  specifically for annotating academic papers within the [Semantic Scholar](https://www.semanticscholar.org) corpus, but can be used with any collection of PDF documents.

### Quick Start

*Quick start will download some pre-processed PDFs and get the UI set up so that you can see them. If you want to pre-process your own PDFs, keep reading! If it's your first time working with PAWLS, we recommend you try the quick start first though.*

First, we need to download some processed PDFs to view in the UI. PAWLS uses the PDFs themselves to render in the browser, as well as using a JSON file of extracted token bounding boxes per page, called `pdf_structure.json`. The [PAWLS CLI](cli/readme.md) can be used to do this pre-processing, but for the quick start, we have done it for you. Download them from the provided AWS S3 Bucket like so:

```bash
aws s3 sync s3://ai2-s2-pawls-public/example-data ./skiff_files/apps/pawls/papers/ --no-sign-request
```

Configuration in PAWLS is controlled by a JSON file, located in the [`api/config`](./api/config/configuration.json) directory. The location that we downloaded the PDFs to above corresponds to the location in the config file, where it is mounted in using [`docker-compose.yaml`](./docker-compose.yaml). So, when PAWLS starts up, the API knows where to look to serve the PDFs we want.

Next, we can start the services required to use PAWLS using `docker-compose`:

```
~ docker-compose up --build
```

This process launches 4 services:
- the `ui`, which renders the user interface that PAWLS uses
- the `api`, which serves PDFs and saves/recieves annotations
- a `proxy` responsible for forwarding traffic to the appropriate services.
- A `grobid` service, running [a fork of Grobid](https://github.com/allenai/grobid). This is not actually necessary for the application, but is useful for the CLI.

You'll see output from each.

Once all of these have come up, navigate to `localhost:8080` in your browser and you should see the PAWLS UI! Happy annotating.


### Getting Started

In order to run a local environment, you'll need to use the [PAWLS CLI](cli/readme.md) to preprocess and assign the PDFs you want to serve. When using PDFs from semantic scholar, the CLI is also used to download the PDFs. The PDFs have to be put in a directory structure within `skiff_files/apps/pawls` (see [PAWLS CLI usage](cli/readme.md#usage) for details).

For instance, you can run the following commands to download, preprocess, and assign PDFs:

```bash
  # Fetches PDFs from semantic scholar's S3 buckets.
  python scripts/ai2-internal/fetch_pdfs.py skiff_files/apps/pawls/papers 34f25a8704614163c4095b3ee2fc969b60de4698 3febb2bed8865945e7fddc99efd791887bb7e14f 553c58a05e25f794d24e8db8c2b8fdb9603e6a29
  # ensure that the papers are pre-processed with grobid so that they have token information.
  pawls preprocess grobid skiff_files/apps/pawls/papers
  # Assign the development user to all the papers we've downloaded.
  pawls assign skiff_files/apps/pawls/papers development_user@example.com --all --name-file skiff_files/apps/pawls/papers/name_mapping.json
```

#### Getting annotation files to s3
PDFs and assignment files from status folder need to be copied to s3 bucket `output_directory` specified in `api/config/configuration.json`
Annotations are going to be uploaded to the `output_directory`.

And then open up the UI locally by running `docker-compose up`.

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

To start a version of the application locally for development purposes, run
this command:

```
~ docker-compose up --build
```

This process launches 3 services, the `ui`, `api` and a `proxy` responsible
for forwarding traffic to the appropriate services. You'll see output
from each.

It might take a minute or two for the application to start, particularly
if it's the first time you've executed this command. Be patience and wait
for a clear message indicating that all of the required services have
started up.

As you make changes the running application will be automatically updated.
Simply refresh your browser to see them.

Sometimes one portion of your application will crash due to errors in the code.
When this occurs resolve the related issue and re-run `docker-compose up --build`
to start things back up.

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
rate limiting. The configuration for the proxy lives [here](./proxy/local.conf) for development and [here](./proxy/prod.conf) for production.

For example, if you wanted to expose the `docs` route `localhost:8000/docs` from your `api` container to users of your app in production, you would add this to `prod.conf`:

```
location /docs/ {
    limit_req zone=api;
    proxy_pass http://api:8000/;
}
```

### Troubleshooting

#### Updating UI Dependencies based on Dependabot Alerts

1. Add the package and version reqs in the `resolutions` field from the [`package.json`](/ui/package.json) file;
2. Run `yarn install` to update the `yarn.lock` file 
3. Start the docker and test whether the UI still works `docker-compose up --build` 

#### Windows EOL format (CRLF) vs Linux (LF)

The application was developed for Linux, and might fail to start on Windows because of line-ending differences.

To fix this, run this command from the root of the repository:

```bash
~ (cd ./ui && yarn && yarn lint:fix) # with parenthesis, to stay in same directory
```

## Cite PAWLS

If you find PAWLS helpful for your research, please consider cite PAWLS. 
```
@misc{neumann2021pawls,
      title={PAWLS: PDF Annotation With Labels and Structure}, 
      author={Mark Neumann and Zejiang Shen and Sam Skjonsberg},
      year={2021},
      eprint={2101.10281},
      archivePrefix={arXiv},
      primaryClass={cs.CL}
}
```

---

PAWLS is an open-source project developed by [the Allen Institute for Artificial Intelligence (AI2)](http://www.allenai.org). AI2 is a non-profit institute with the mission to contribute to humanity through high-impact AI research and engineering.

## Replica Management

Because the application is used in short bursts for annotation projects, we manually turn
the application on and off. We do this by managing the number or replicas, toggling it from
`0` to `1` and vice versa.

To adjust the number of replicas, edit the `skiff.json` and change the replica
count. For instance, you can turn the application "off" like so:

```diff
{
    "appName": "pawls",
    "contact": "lucas",
    "team": "s2research",
-    "replicas": 1
+    "replicas": 0
}
```

...and turn it back "on" by reversing that change:

```diff
{
    "appName": "pawls",
    "contact": "lucas",
    "team": "s2research",
-    "replicas": 0
+    "replicas": 1
}
```

The change will be applied after committing and pushing your change. It usually
takes around 5 minutes or so for things to take effect.

You can confirm the change by visiting [Marina](https://marina.apps.allenai.org/a/pawls)
and inspecting the "Replicas" list for the `skimming-annotations` environment. 
The number of replicas displayed there should match match the value in `skiff.json`.

