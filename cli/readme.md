## PAWLS CLI

The PAWLS CLI helps manage annotation tasks based on PDFs.

### Secrets

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

1. Download PDFs based on <PDF_SHA>s into the <SAVE_PATH> (e.g., `skiff_files/apps/pawls/papers` ). If you work at AI2, see the internal usage script for doing this [here](../../scripts/ai2-internal). Otherwise, pdfs are expected to be in a directory structure with a single pdf per folder, where each folder's name is a unique id corresponding to that pdf. For example:
```
    top_level/
    ├───pdf1/
    │     └───pdf1.pdf
    └───pdf2/
    │     └───pdf2.pdf
```
By default, pawls will use the name of the containing directory to refer to the pdf in the ui.

2. Process the token information for each PDF document with the given PDF preprocessor `grobid/pdfplumber`:
    ```bash
    pawls preprocess grobid skiff_files/apps/pawls/papers
    ```
3. Assign annotation tasks (<PDF_SHA>s) to specific users <user>:
    ```bash
    pawls assign ./skiff_files/apps/pawls/papers <user> <PDF_SHA>
    ```
    Optionally at this stage, you can provide a `--name-file` argument to `pawls assign`,
    which allows you to specify a name for a given pdf (for example the title of a paper).
    This file should be a json file containing `sha:name` mappings.
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