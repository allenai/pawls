
#### Fetching PDFs (AI2 Internal)

The `fetch_pdfs.py` script fetches S2 pdfs for use by PAWLS using paper shas.
This requires access to the S2 pdf bucket, so is for internal use only. However,
you can use PAWLS without using this script if you already have pdfs locally! This is simply
a utility for S2 Researchers.

The `fetch_pdfs.py` script requires a AWS key with read access to the S2 Pdf bucket. Your `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` which you use for day-to-day AI2 work will
be suitable - just make sure they are set as environment variables when running the PAWLS CLI.
