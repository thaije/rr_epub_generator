# rr_epub_generator

Epub generator for webpages scraped from RoyalRoads

# How to install

Make a virtual env with Python3:

- `pip install virtualenv virtualenvwrapper`
- `export WORKON_HOME=$HOME/.virtualenvs`
- `export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3`
- `source /usr/local/bin/virtualenvwrapper.sh`
- `mkvirtualenv rr_epub_gen -p python3`
- `workon rr_epub_gen`

Install the requirements:

- `pip install -r requirements.txt`

# How to run

- Change the `starting_url` in `crawl_and_gen_epub_pages.html` to link to the first chapter you want to crawl. The script will automatically look for next chapters untill no new chapters found.
- `python crawl_and_gen_epub_pages.html`

# How it works

Ebooks are basically folders with html pages (a html file per chapter), a table of contents, and some visuals such as a cover image.
A program such as the free open-source [Sigil](https://sigil-ebook.com/) can automatically create a table of contents, and you can add a cover image there as well. Only thing left is to create a html page for each chapter.

This script:

1. Visits your specified starting Royal Roads page, such as [chapter 1 of The Arcane Emperor](https://www.royalroad.com/fiction/8463/the-arcane-emperor/chapter/94620/chapter-1-new-beginnings).
2. Scrapes this chapter page from Royal Roads, and copies the title and content from the html.
3. Creates a new html page for that chapter with the parsed chapter title and content in the format as shown in `example_file.html`.
4. Tries to find Next Chapter button, and if available, go back to step 2 for the new chapter.

The result is that `/output` folder is filled with html pages, for each chapter one. Copy paste these pages into your Sigil Epub, save as epub, and done.
