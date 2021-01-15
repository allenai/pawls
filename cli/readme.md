## PAWLS CLI

The PAWLS CLI helps manage annotation tasks based on PDFs.

### Installation

1. Install dependencies

    ```bash
    cd pawls/cli
    python setup.py install
    ```

2. (Optional) Install poppler, the PDF renderer, which is used to export the annotations into a COCO-format Dataset by converting the PDF pages to images.
Please follow the [instructions here](https://github.com/Belval/pdf2image#windows). 

3. (Optional) Install Tesseract, the OCR software, which is used to perform OCR on scanned documents.
Please follow the [instructions here](https://tesseract-ocr.github.io/tessdoc/Installation.html).

### Usage

1. Download PDFs based on <PDF_SHA>s into the <SAVE_PATH> (e.g., `skiff_files/apps/pawls/papers` ). If you work at AI2, see the internal usage script for doing this [here](../../scripts/ai2-internal). Otherwise, pdfs are expected to be in a directory structure with a single pdf per folder, where each folder's name is a unique id corresponding to that pdf. For example:
```
    top_level/
    ├───pdf1/
    │     └───pdf1.pdf
    └───pdf2/
          └───pdf2.pdf
```
By default, pawls will use the name of the containing directory to refer to the pdf in the ui.

2. Process the token information for each PDF document with the given PDF preprocessor.
    ```bash
    pawls preprocess <preprocessor-name> skiff_files/apps/pawls/papers
    ```
    Currently we support the following preprocessors:
    1. pdfplumber
    2. grobid *Note: to use the grobid preprocessor, you need to run `docker-compose up` in a separate shell, because grobid needs to be running as a service.*
    3. ocr *Note: you might need to install [tesseract-ocr](https://tesseract-ocr.github.io/tessdoc/Installation.html) for using this preprocessor.*

3. Assign annotation tasks (<PDF_SHA>s) to specific users <user>:
    ```bash
    pawls assign ./skiff_files/apps/pawls/papers <user> <PDF_SHA>
    ```
    Optionally at this stage, you can provide a `--name-file` argument to `pawls assign`,
    which allows you to specify a name for a given pdf (for example the title of a paper).
    This file should be a json file containing `sha:name` mappings.
4. (optional) Create pre-annotations for the PDFs based on some model predictions `anno.json`:
    ```bash
    pawls preannotate <labeling_folder> <labeling_config> anno.json -u <user>
    ```
    You could find an example for generating the pre-annotations in `scripts/generate_pdf_layouts.py`.
5. Export the annotated dataset to the COCO format:

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