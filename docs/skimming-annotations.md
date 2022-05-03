# Paper Skimming: Annotation Guidelines

This document contains the annotation guidelines for the paper skimming project.
If you have been hired to provide annotation services, please read it carefully.
For any question, email us to [paper-skimming-annotations@allenai.org][7], or get in touch through the hiring platform you signed up with (e.g. UpWork).

Jump to:

- [Annotation Guidelines](#annotation-guidelines)
- [Workflow](#workflow)
- [Goal](#goal)
- [Tips](#tips)

--------------------

## Annotation Guidelines

To help you complete this task, imagine being part of the following scenario.

You have been hired by a scientific communication magazine (for example, [Communications of the ACM][8] or [MIT Technology Review][9]) to help **create abridged versions of scientific papers**. These are shorter versions of full academic papers that are often read by researchers from the same academic field who might not have time to read full-length manuscript.

Your boss, the editor, has given you a target length of **200 words per paper  page**,
with some wiggle room. For example:

|Length of Paper    | Word count target |
|:-----------------:|:-----------------:|
|4 pages            |  800 ± 40 words   |
|8 pages            |  1,600 ± 80 words |
|12 pages           | 2,400 ± 120 words |

You have to **decide which sentences from the manuscript are significant**, and
thus should be kept while fitting within the target length. Anything you do not
select will be mercilessly thrown away by the ruthless editor. Further, you have
to meet the following conditions when selecting sentences:

1. You can only keep **full sentences**, not fragments.
    - If only a portion of a sentence is significant, also highlight the rest of the sentence.
2. You have to keep **at least 1 sentence for each section heading**.
    - This applies to all section headings with some text underneath it. For example has sections 3, and 3.1, you should keep at least one sentence for each heading: ![A picture showing how to highlight sentences from each section](static/one-sentence-per-par.png)
    - In case a section has no text underneath, you can skip it; in this example example, Section 3 has no sentences to highlight, so one can move to 3.1 instead:
    ![A picture showing a section with nothing to highlight](static/no-subsentence.png)
3. You can only **select sentences from the main text**. Leave the title,
abstract, figures, or table captions as they are: the editor has decided
to reproduce them in full (*phew!*)

Try to keep within the target length! This magazine is still printed and
distributed to subscribers, so every drop of ink counts.

Ideally, someone can read the set of chosen sentences like a coherent
document--our editor is lazy, and does not want to rewrite any of the shortened
paper before it is published.

--------------------

## Workflow

### Step 1: Download Papers to Annotate

Download all papers from [this Google Drive link][10].
Once you open the link, you can start the download by clicking in the top right corner:

![Download link on Google Drive](static/how-to-download.png)

### Step 2: Upload a Paper to the Annotation interface

Visit [pawls.skimming-annotations.apps.allenai.org/upload][11] to upload a paper.

![Upload Interface](static/upload-interface.png)

Please keep in mind the following order and target length when working on papers:

| Annotation Order |     File Name     |            Target Length           |
|:----------------:|:-----------------:|:----------------------------------:|
|        1         | short_paper_1.pdf | 1,000 words (min 950; max 1,050)   |
|        2         |  long_paper_1.pdf | 1,600 words (min 1,520; max 1,680) |
|        3         |  long_paper_2.pdf | 1,600 words (min 1,520; max 1,680) |
|        4         |  long_paper_3.pdf | 1,600 words (min 1,520; max 1,680) |
|        5         |  long_paper_4.pdf | 1,600 words (min 1,520; max 1,680) |
|        6         |  long_paper_5.pdf | 1,600 words (min 1,520; max 1,680) |


### Step 3: Familiarize Yourself with the Annotation Interface

![Annotation interface](static/full-interface.png)


### Step 4: Highlighting Sentences

To highlight a sentence, hold your mouse down while spanning across the text you want to highlight.

![A gif showing how to highlight sentences.](static/highlighting.gif)

### Step 5: Mark a Paper as Finished When Done

Don't forget to use the toggle to mark a paper as finished as shown in [Step 3](#step-3-familiarize-yourself-with-the-annotation-interface).


--------------------

## Goal

We are looking at ways to improve first-time reading experience of PDFs;
in particular, we want to create a system that highlights important passages in papers.
The data you annotate will help us power this new system.

Here's an example of a potential interface for this system:

![A zoomed-in PDF with about a third of its sentenced highlighted in different colors: red, blue, green](static/interface.png)

Highlighted passages could contain key background information, contribution statements, important results, and so on.

--------------------

## Tips

- **Try adopting a two passes strategy when selecting sentences**: During the first phase, highlight all sentences you think are significant without relying on the word count too much; during the second phase, remove/add sentences till you get to the target length.

[1]: https://pawls.skimming-annotations.apps.allenai.org/pdf/07fe8482df88405b718fe77db2f46e51fee4aed512dc7179aae3c70804ae0e8a
[2]: https://pawls.skimming-annotations.apps.allenai.org/pdf/056002826389e5c8222071117b2c5a358fcbfd72536d7d87ed6ab5f5b8afaa32
[3]: https://pawls.skimming-annotations.apps.allenai.org/pdf/4f276356d2b1a8acd7d6c2d583abf23356a833428624f8ff12d9e57371ac8300
[4]: https://pawls.skimming-annotations.apps.allenai.org/pdf/b15b4378988ed4e553dd312eaf334411abcf1fb28c53b846d360435eb55cd193
[5]: https://pawls.skimming-annotations.apps.allenai.org/pdf/416b17a3fa07da8c811381144c0e042bbfecd2df3a5028ecf03fb5735d7309a8
[6]: https://pawls.skimming-annotations.apps.allenai.org/pdf/9c420ad8eb59c3a5361c45073f799ea52933029b346b430bfe2002744f9cfdef
[7]: mailto:paper-skimming-annotations@allenai.org
[8]: https://cacm.acm.org
[9]: https://www.technologyreview.com
[10]: https://drive.google.com/file/d/1e4XWqpucOFef1ZmZ9yAn0Er3p736itPz/view?usp=sharing
[11]: https://pawls.skimming-annotations.apps.allenai.org/upload
