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

1. Place or download PDFs into `skiff_files/apps/pawls/papers` as described below. If you work at AI2, see the internal usage script for doing this [here](../../scripts/ai2-internal). 

Otherwise, you can add PDFs using the command:
```bash
pawls add <pdf-or-directory>
```

By default, pawls will create a unique id per PDF by hashing the PDF, and use that hash to refer to the PDF in the UI.
You can instead retain the original PDF name by passing the `--no-hash` flag to `pawls add`.

2. [preprocess] Process the token information for each PDF document with the given PDF preprocessor.
    ```bash
    pawls preprocess <preprocessor-name> skiff_files/apps/pawls/papers
    ```
    Currently we support the following preprocessors:
    1. pdfplumber
    2. grobid *Note: to use the grobid preprocessor, you need to run `docker-compose up` in a separate shell, because grobid needs to be running as a service.*
    3. ocr *Note: you might need to install [tesseract-ocr](https://tesseract-ocr.github.io/tessdoc/Installation.html) for using this preprocessor. It also accepts extra parameters for language and page segmentation mode (eg: `pawls preprocess ocr <path> ocr-param lang=eng+ara psm=11`). If you want to use Google Cloud Vision instead, you can run the command with `ocr-param engine=cloud-vision` and `lang="en+ar"` after downloading your credential file from GCP to `<current-working-dir>/gcv-*.json`.*

3. [assign] Assign annotation tasks (<PDF_SHA>s) to specific users <user>:
    ```bash
    pawls assign ./skiff_files/apps/pawls/papers <user> <PDF_SHA>
    ```
    Optionally at this stage, you can provide a `--name-file` argument to `pawls assign`,
    which allows you to specify a name for a given PDF (for example the title of a paper).
    This file should be a JSON file containing `sha:name` mappings.

4. (optional) [preannotate] Create pre-annotations for the PDFs based on some model predictions `anno.json`:
    ```bash
    pawls preannotate <labeling_folder> <labeling_config> anno.json -u <user>
    ```
    You could find an example for generating the pre-annotations in `scripts/generate_pdf_layouts.py`.

5. [status] Check annotation status for the <labeling_folder>:
    ```bash
    pawls status <labeling_folder>
    ```

    1. Save the labeling record table:
        ```bash
        pawls status <labeling_folder> --output record.csv
        ```

6. [metric] Check Inter Annotator Agreement (IAA):
    ```bash
    pawls metric <labeling_folder> <config_file> \
        --textual-categories cat1,cat2 --non-textual-categories cat3,cat4
    ```
    For blocks, we measure the consistency using the [mAP scores](https://jonathan-hui.medium.com/map-mean-average-precision-for-object-detection-45c121a31173). It is a common metric 
    in object detection tasks, evaluating the block category consistency at different overlapping 
    levels.


    For textual regions, we measure the consistency based on the token categories. 
    We will assign PDF tokens with the categories of the contained blocks, and compare
    the label of the same token across annotators. The agreement level is measured via 
    token accuracy. 

    It will print a matrix, where the (i,j)-th element in the table is calculated by 
    treating the annotations from i as the "ground-truth"s, and those from j are 
    considered as "predictions"

    1. Save the IAA report to `<save-folder>`:
        ```bash
        pawls metric <labeling_folder> <config_file> \
            --textual-categories cat1,cat2 --non-textual-categories cat3,cat4 \
            --save <save-folder>
        ```
        It will create `block-eval.csv` and `textual-eval.csv` in the folder for block and textual 
        region IAA. 
    
    2. Specify annotators for calculating IAA:
        ```bash
        pawls metric <labeling_folder> <config_file> \
            --textual-categories cat1,cat2 --non-textual-categories cat3,cat4 \
            --u <annotator1> --u <annotator2>
        ```
        
7. [export] Export the annotated dataset to the specified format. Currently we support export to `COCO` format and the `token` table format. 

    1. Export all annotations of a project of all annotators:
        ```bash
        pawls export <labeling_folder> <labeling_config> <output_path> <format>
        ```

    2. Export only finished annotations of a given annotator, e.g. markn:
        ```bash
        pawls export <labeling_folder> <labeling_config> <output_path> <format> -u markn
        ```

    3. Export all annotations (include unfinished annotations) from a given annotator: 
        ```bash
        pawls export <labeling_folder> <labeling_config> <output_path> <format> -u markn --include-unfinished
        ```

## Dataset structure

PDFs are expected to be in a directory structure with a single PDF per folder, where each folder's name is a unique ID corresponding to that PDF. For example:
```
    top_level/
    ├───pdf1/
    │     └───pdf1.pdf
    └───pdf2/
          └───pdf2.pdf
```

Using only `pawls add` to add PDFs will maintain this structure by default.
