import React, { useState, useRef, useCallback, useEffect } from 'react';
import styled from 'styled-components';

import {Button} from "@allenai/varnish";

import pdfjsWorker from "pdfjs-dist";
import pdfjs from "pdfjs-dist";

// This should be the worker above, but TS complains because we are assigning
// a js module to a string value. So we just use some other CDN hosted one.
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`;


const Home = () => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const annotationsRef = useRef<HTMLDivElement>(null);
  
    const [pdfRef, setPdfRef] = useState<pdfjsWorker.PDFDocumentProxy>();
    const [currentPage, setCurrentPage] = useState(1);

    const url = "/api/pdf/34f25a8704614163c4095b3ee2fc969b60de4698"

    const renderPage = useCallback((pageNum, pdf=pdfRef) => {
      pdf && pdf.getPage(pageNum).then((page: any) => {

        const canvas = canvasRef.current;
        const annotator = annotationsRef.current;
        if (canvas !== null && annotator !== null) {

        // Calculate dimensions of the PDF.
        // See: https://github.com/mozilla/pdf.js/blob/7edc5cb79fe829d45fed85e2b4b6d8594522cc10/src/display/api.js#L1039
        const dims = {
            width: page.view[2] - page.view[1],
            height: page.view[3] - page.view[0]
        };
        const scale = Math.max(
            annotator.clientWidth / dims.width,
            annotator.clientHeight / dims.height
        );
        const viewport = page.getViewport({ scale });
        // TODO(Mark/Sam): Add an event listener for resizing the window
        // and handle it. 
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        const renderContext = {
        canvasContext: canvas.getContext('2d'),
        viewport: viewport
        };
        page.render(renderContext);
        }
      });   
    }, [pdfRef]);
  
    useEffect(() => {
      renderPage(currentPage, pdfRef);
    }, [pdfRef, currentPage, renderPage]);
  
    useEffect(() => {
      const loadingTask = pdfjs.getDocument(url);
      loadingTask.promise.then(loadedPdf => {
        setPdfRef(loadedPdf);
      }, (reason) => {console.error(reason)});
    }, [url]);
  
    const nextPage = () => pdfRef && currentPage < pdfRef.numPages && setCurrentPage(currentPage + 1);
    const prevPage = () => currentPage > 1 && setCurrentPage(currentPage - 1);
  
    return (
        <React.Fragment>
            <div ref={annotationsRef}>
                <canvas ref={canvasRef}/>
            </div>
            <Button onClick={prevPage}>
                Previous
            </Button>
            <Button onClick={nextPage}>
                Next
            </Button>
        </React.Fragment>
    )
  }

export default Home;