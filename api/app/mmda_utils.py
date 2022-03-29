from collections import defaultdict
from enum import IntEnum
from functools import partial
import logging
from typing import Optional, Sequence, Union, Any

from mmda.parsers.pdfplumber_parser import PDFPlumberParser
from mmda.types.annotation import SpanGroup
from mmda.rasterizers.rasterizer import PDF2ImageRasterizer
from mmda.predictors.lp_predictors import LayoutParserPredictor
from mmda.predictors.hf_predictors.vila_predictor import IVILAPredictor, HVILAPredictor


# PDF is verbose, so we need to quiet it here
for name in logging.root.manager.loggerDict:
    if name.startswith('pdfminer'):
        _chatty_logger = logging.getLogger(name)
        logging_level = max(_chatty_logger.level, logging.INFO)
        _chatty_logger.setLevel(logging_level)

logger = logging.getLogger(__file__)


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


class MmdaUtils:
    def __init__(
        self,
        layout_parser: str = 'lp://efficientdet/PubLayNet',
        vila_predictor: str = "allenai/ivila-block-layoutlm-finetuned-docbank",
        rasterize_dpi: int = 72,
        valid_doc_labels: Optional[Sequence[Union[str, DocLabels]]] = None,
    ):
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

        self.layout_predictor = LayoutParserPredictor.from_pretrained(
            "lp://efficientdet/PubLayNet"
        )

        self.parse_fn = PDFPlumberParser().parse
        self.rasterize_fn = partial(PDF2ImageRasterizer().rasterize,
                                    dpi=rasterize_dpi)

        valid_doc_labels = (valid_doc_labels or
                            [DocLabels.paragraph, DocLabels.list])
        self.valid_doc_labels = [DocLabels(l) for l in valid_doc_labels]

    async def __call__(self, pdf_file: str) -> Any:

        logging.info(f'Parsing {pdf_file} with pdfplumber')
        doc = self.parse_fn(pdf_file)

        logging.info(f'Rasterizing {pdf_file} to images')
        images = self.rasterize_fn(input_pdf_path=pdf_file, dpi=72)
        doc.annotate_images(images)

        # Obtaining Layout Predictions
        layout_regions = self.layout_predictor.predict(doc)
        doc.annotate(blocks=layout_regions)

        # annotate with vila
        spans = self.vila_predictor.predict(doc)
        doc.annotate(preds=spans)

        pages = []

        for pid in range(len(doc.pages)):
            pw, ph = doc.images[pid].size

            page = {'page': {"width": pw, "height": ph, "index": pid},
                    'tokens': []}

            for pred in doc.pages[pid].preds:
                page['tokens'].extend({
                    'text': doc.symbols[t.spans[0].start:t.spans[0].end],
                    'width': t.spans[0].box.w * pw,
                    'height': t.spans[0].box.h * ph,
                    'x': t.spans[0].box.l * pw,
                    'y': t.spans[0].box.t * ph,
                    'valid': (1 if DocLabels(pred.type) in
                              self.valid_doc_labels else 0)
                } for t in pred.tokens)

            pages.append(page)

        return pages
