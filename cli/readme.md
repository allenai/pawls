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

1. Install dependencies

    ```bash
    cd pawls/cli
    python setup.py install
    export GITHUB_ACCESS_TOKEN=<password from 1password>
    pip install git+https://${GITHUB_ACCESS_TOKEN}@github.com/allenai/s2-pdf-structure-service@master#subdirectory=clients/python
    ```

2. Install poppler, the PDF renderer, which is used to export the annotations into a COCO-format Dataset by converting the PDF pages to images.
Please follow the [instructions here](https://github.com/Belval/pdf2image#windows). 

### Usage

1. Download PDF document and metadata based on <PDF_SHA>s into the <SAVE_PATH> (e.g., `skiff_files/apps/pawls/papers` ):
    ```bash
    pawls fetch skiff_files/apps/pawls/papers <PDF_SHA>    
    ```
2. Process the token information for each PDF document:
    ```bash
    pawls preprocess grobid skiff_files/apps/pawls/papers
    ```
3. Assign annotation tasks (<PDF_SHA>s) to specific users <user>:
    ```bash
    pawls assign ./skiff_files/apps/pawls/papers <user> <PDF_SHA>
    ```
4. Export the annotated dataset to the COCO format:

    1. Export all annotations of a project of the default annotator (development_user):
        ```bash
        pawls export <labeling_folder> <labeling_config> <output_path>
        ```

    2. Export only finished annotations of from a given annotator, e.g. markn:
        ```bash
        pawls export <labeling_folder> <labeling_config> <output_path> -u markn
        ```

    3. Export all annotations of from a given annotator: 
        ```bash
        pawls export <labeling_folder> <labeling_config> <output_path> -u markn --all
        ```