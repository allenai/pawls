class Config:
    """
    Configuration for anything related to pdfs. We wrap this up in a class
    so that it's easier to test.

    PDF_STORE_PATH: str
        Where the raw pdfs are stored for annotation. In production, this uses
        Skiff Files.
    """

    PDF_STORE_PATH: str = "/skiff_files/apps/pawls/pdfs/"
    PDF_METADATA_PATH: str = "/skiff_files/apps/pawls/metadata/"
