## PAWLS CLI

The PAWLS CLI helps manage annotation tasks based on PDFs.

### Secrets

The Pawls CLI requires a AWS key with read access to the S2 Pdf buckets. There is a key pair for this task specifically [here](https://allenai.1password.com/vaults/4736qu2dqfkjjxqs63w4c2gwt4/allitems/yq475h75a2zaeuh4zhq23otkki), but your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` which you use for day-to-day AI2 work will
be suitable - just make sure they are set as environment variables when running the PAWLS CLI.

The PAWLS CLI requires the python client of the [S2 Pdf Structure Service](https://github.com/allenai/s2-pdf-structure-service),
which you can find [here](https://allenai.1password.com/vaults/4736qu2dqfkjjxqs63w4c2gwt4/allitems/i73dbwizxzlu2savgd2pbrzyzq).
In order to install the CLI tool, you will need to export this as a bash variable.

```
export GITHUB_ACCESS_TOKEN=<password from 1password>
pip install git+https://${GITHUB_ACCESS_TOKEN}@github.com/allenai/s2-pdf-structure-service@master#subdirectory=clients/python
```


### Installation

```
cd pawls/cli
python setup.py install
export GITHUB_ACCESS_TOKEN=<password from 1password>
pip install git+https://${GITHUB_ACCESS_TOKEN}@github.com/allenai/s2-pdf-structure-service@master#subdirectory=clients/python