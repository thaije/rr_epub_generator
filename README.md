# Royal Roads Epub Generator

Simple epub generator with webscraper for novels at RoyalRoads

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

- Change the `starting_url` in `crawl_and_gen_epub_pages.html` to link to the first chapter of the novel you want crawl. The script will automatically look for next chapters untill no new chapters found.
- `python crawl_and_gen_epub_pages.html`
- Download [Sigil](https://sigil-ebook.com/), create a new Epub, and copy paste the generated html files into the Text folder of your epub 
- (optional) Add a title to your epub file:
    - Change the `docTitle` in the `toc.ncx` file, and the `<dc:title>` in `content.opf`. 
- (optional) Add a cover photo to your epub:
    - Add an image to the `Images` folder in your epub in Sigil
    - In the `Text` folder of your epub in Sigil, add a new page called cover.xhtml. 
    - Replace the content with e.g. something like below (making sure the file name is correct):
```html
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
  "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">

<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Cover</title>
</head>

<body>
  <img style="width:100%; height:auto;" alt="cover" src="../Images/cover.png"/>
</body>
</html> 
```


# How it works

Ebooks are basically folders with html pages (a html file per chapter), a table of contents, and some visuals such as a cover image.
A program such as the free open-source [Sigil](https://sigil-ebook.com/) can automatically create a table of contents, and you can add a cover image there as well. Only thing left is to create a html page for each chapter.

This script:

1. Visits your specified starting Royal Roads page, such as [chapter 1 of The Arcane Emperor](https://www.royalroad.com/fiction/8463/the-arcane-emperor/chapter/94620/chapter-1-new-beginnings).
2. Scrapes this chapter page from Royal Roads, and copies the title and content from the html.
3. Creates a new html page for that chapter with the parsed chapter title and content in the format as shown in `example_file.html`.
4. Tries to find Next Chapter button, and if available, go back to step 2 for the new chapter.

The result is that `/output` folder is filled with html pages, for each chapter one. Copy paste these pages into your Sigil Epub, save as epub, and done.

# Troubleshooting
Epubs are not exactly the same as html, and some html can cause errors. For example, the `<hr>` tag ( a horizontal line) or the `<br>` tag (a newline) need to be replaced with `<hr/>` and `<br/>`. 
If you get errors such as this in Sigil or your epub reader, you can add some custom rules for removing non-epub friendly HTML on [this line](https://github.com/thaije/rr_epub_generator/blob/main/crawl_and_gen_epub_pages.py#L58).
