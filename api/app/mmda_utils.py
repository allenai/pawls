import asyncio
from email.policy import default
import pickle
import logging
import multiprocessing
import os
import warnings
from concurrent.futures import ProcessPoolExecutor
from enum import IntEnum
from tempfile import NamedTemporaryFile
from typing import List, Optional, Sequence, Tuple, Union

import torch
from pydantic import BaseModel, Field, validator
from PyPDF2 import PdfFileReader, PdfFileWriter
from minimal_server import minimal_server, MinimalClient
import click

from mmda.parsers.pdfplumber_parser import PDFPlumberParser
from mmda.predictors.hf_predictors.vila_predictor import (HVILAPredictor,
                                                          IVILAPredictor)
from mmda.predictors.lp_predictors import LayoutParserPredictor
from mmda.rasterizers.rasterizer import PDF2ImageRasterizer
from mmda.types.document import Document


class PageSpec(BaseModel):
    width: int
    height: int
    index: int


class PageToken(BaseModel):
    text: str
    width: float
    height: float
    x: float
    y: float
    valid: int

    @validator('valid')
    def valid_flag_range(cls, value):
        assert value in {-1, 0, 1}
        return int(value)


class Page(BaseModel):
    page: PageSpec
    tokens: List[PageToken] = Field(default_factory=lambda: [])


class DocLabels(IntEnum):
    paragraph: int = 0
    title: int = 1
    equation: int = 2
    reference: int = 3
    section: int = 4
    list: int = 5
    table: int = 6
    caption: int = 7
    author: int = 8
    abstract: int = 9
    footer: int = 10
    date: int = 11
    figure: int = 12


def get_logger(obj) -> logging.Logger:
    cls_ = obj if isinstance(obj, str) else obj.__class__.__name__
    # proc_ = multiprocessing.current_process().name
    logger = multiprocessing.get_logger()

    formatter = logging.Formatter(
        f'[%(levelname)s/%(processName)s/{cls_}] %(message)s'
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger


def split_doc_on_pages(pdf_path: str) -> Sequence[Tuple[int, str]]:
    pages = []
    pdf_name = os.path.splitext(os.path.split(pdf_path)[1])[0]
    with open(pdf_path, 'rb') as in_file:
        reader = PdfFileReader(in_file)
        for i in range(reader.getNumPages()):
            with NamedTemporaryFile(delete=False, prefix=f'{pdf_name}_', suffix='.pdf') as tmp:
                writer = PdfFileWriter()
                writer.addPage(reader.getPage(i))
                writer.write(tmp)
                pages.append((i, tmp.name))
    return pages


class MmdaUtils:
    def __init__(
        self,
        layout_parser: str = 'lp://efficientdet/PubLayNet',
        vila_predictor: str = "allenai/ivila-block-layoutlm-finetuned-docbank",
        rasterize_dpi: int = 72,
        valid_doc_labels: Optional[Sequence[Union[str, DocLabels]]] = None,
        mp_context: str = None
    ):
        self.mp_context = torch.multiprocessing.get_context(mp_context)

        os.environ['TOKENIZERS_PARALLELISM'] = 'false'
        if 'ivila' in vila_predictor:
            vila_cls = IVILAPredictor
        elif 'hvila' in vila_predictor:
            vila_cls = HVILAPredictor
        else:
            msg = f'{vila_predictor} is not HVILA or IVILA'
            raise TypeError(msg)

        if 'block' in vila_predictor:
            added_special_sepration_token = "[BLK]"
            agg_level = "block"
        elif 'row' in vila_predictor:
            added_special_sepration_token = '[SEP]'
            agg_level = 'row'
        else:
            msg = f'{vila_predictor} is not `block` or `row`'
            raise TypeError(msg)

        self.vila_predictor = vila_cls.from_pretrained(
            model_name_or_path=vila_predictor,
            added_special_sepration_token=added_special_sepration_token,
            agg_level=agg_level
        )

        self.layout_predictor = \
            LayoutParserPredictor.from_pretrained(layout_parser)

        self.parser = PDFPlumberParser()
        self.rasterizer = PDF2ImageRasterizer()
        self.rasterize_dpi = rasterize_dpi

        valid_doc_labels = (valid_doc_labels or
                            [DocLabels.paragraph, DocLabels.list])
        self.valid_doc_labels = [DocLabels(l) for l in valid_doc_labels]

    def eval(self):
        self.vila_predictor.model.eval()
        self.layout_predictor.model.model.eval()

    def share_memory(self):
        self.vila_predictor.model.share_memory()
        self.layout_predictor.model.model.share_memory()

    def get_logger(self) -> logging.Logger:
        return get_logger(self)

    # async def async_process_pdf(
    #     self,
    #     pdf_file: str,
    #     nproc: int = 0,
    #     use_pyd: bool = False,
    #     loop: Optional[asyncio.BaseEventLoop] = None) -> Sequence[Page]:
    #     with ProcessPoolExecutor(max_workers=nproc,
    #                              mp_context=self.mp_context) as pool:
    #         # futures = [loop.run_in_executor(pool, process_page, fn, queue) for fn in temp_pages]
    #         futures = [
    #             loop.run_in_executor(pool, mmda.run, page)
    #             # loop.run_in_executor(pool, test, queue, page[0])
    #             for page in temp_pages
    #         ]
    #         data = await asyncio.gather(*futures)

    def process_pdf(self,
                    pdf_file: str,
                    nproc: int = 0,
                    use_pyd: bool = False,
                    loop: Optional[asyncio.BaseEventLoop] = None) -> Sequence[Page]:
        if nproc == 0:
            self.get_logger().info('Processing on main process')
            doc = self._process_file(pdf_file)
            pages = [self._export_page_annotations(doc, pid)
                     for pid in range(len(doc.pages))]
        else:
            self.get_logger().info(f'Splitting {pdf_file} on pages...')
            pages_fn = split_doc_on_pages(pdf_file)
            self.get_logger().info(f'Using multiprocesssing with {nproc}...')
            with ProcessPoolExecutor(max_workers=nproc,
                                     mp_context=self.mp_context) as ex:
                pages = list(ex.map(self.process_page, pages_fn))

        self.get_logger().info(f'Done with all pages.')

        if not use_pyd:
            pages = [page.dict() for page in pages]

        return pages

    def _export_page_annotations(self, doc: Document, pid: int) -> Page:
        pw, ph = doc.images[pid].size

        page = Page(page=PageSpec(width=pw, height=ph, index=pid))

        for pred in doc.pages[pid].preds:
            page.tokens.extend(PageToken(
                text=doc.symbols[t.spans[0].start:t.spans[0].end],
                width=t.spans[0].box.w * pw,
                height=t.spans[0].box.h * ph,
                x=t.spans[0].box.l * pw,
                y=t.spans[0].box.t * ph,
                valid=(1 if DocLabels(pred.type) in
                       self.valid_doc_labels else 0)
            ) for t in pred.tokens)

        return page

    def process_page(self, page_info: Tuple[int, str]) -> Page:
        page_index, pdf_file = page_info
        try:
            doc = self._process_file(pdf_file)
            page = self._export_page_annotations(doc, 0)
            page.page.index = page_index
            return page
        except Exception as e:
            self.get_logger().fatal(e)
            raise e

    def _process_file(self, pdf_file: str) -> Document:
        logging.getLogger("pdfminer").setLevel(logging.ERROR)
        logger = self.get_logger()

        logger.info(f'Parsing {pdf_file} with pdfplumber')
        doc = self.parser.parse(pdf_file)

        logger.info(f'Rasterizing {pdf_file} to images')
        images = self.rasterizer.rasterize(input_pdf_path=pdf_file,
                                           dpi=self.rasterize_dpi)
        doc.annotate_images(images)

        # Obtaining Layout Predictions
        logger.info(f'Predicting layout for {pdf_file}')
        with torch.no_grad(), warnings.catch_warnings():
            # effdet complains about __floordiv__
            warnings.simplefilter("ignore")
            layout_regions = self.layout_predictor.predict(doc)

        doc.annotate(blocks=layout_regions)

        logger.info(f'Predicting sections for {pdf_file}')
        # annotate with vila
        with torch.no_grad():
            spans = self.vila_predictor.predict(doc)
        doc.annotate(preds=spans)

        logger.info(f'Done with {pdf_file}')

        return doc


def mmda_client(port: int = 5555, buffersize: int = 2048) -> MmdaUtils:
    return MinimalClient(MmdaUtils, port=port, buffersize=buffersize)


@click.command()
@click.option('--port', default=5555, type=int)
@click.option('--buffersize', default=2048, type=int)
@click.option('--host', default='localhost', type=str)
@click.option('--mp-context', default='spawn', type=str)
@click.option('--pickle-protocol', default=pickle.HIGHEST_PROTOCOL, type=int)
def mmda_server(port: int,
                buffersize: int,
                host: str,
                mp_context: str,
                pickle_protocol: int):

    torch.multiprocessing.set_start_method(mp_context)

    logger = get_logger('__main__')

    logger.info('Getting MMDA...')
    mmda = MmdaUtils(mp_context=mp_context)
    mmda.eval()
    mmda.share_memory()
    logger.info('Starting server...')
    minimal_server(mmda,
                   port=port,
                   buffersize=buffersize,
                   host=host,
                   pickle_protocol=pickle_protocol)


if __name__ == '__main__':
    mmda_server()