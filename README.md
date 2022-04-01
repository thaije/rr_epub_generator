# Royal Roads Epub Generator

Simple epub generator with webscraper for novels at RoyalRoads

# How to install

- Install Python >= 3.6
- Install the requirements with `pip install -r requirements.txt`

# How to run

- Change some params in `gen_epub.py`:
  - Change the `book_name` to the title of your book. Example: `book_name = "The Arcane Emperor"`
  - Change the `starting_url` so it points at the url of the first page you want to include. **Not inlcuding** the base url. `starting_url = "/fiction/8463/the-arcane-emperor/chapter/94620/chapter-1-new-beginnings"`
- run `python get_epub.py`

Copy paste the generated epub to your ereader of preference.

# How it works

Epubs are basically zip files that look fancy. In the zip you have seperate html pages for each book chapter, in addition to some extra XML files so your ereader knows which chapters are available and what the cover image is etc.
For creating this script I first figured out how to create a epub file with Python with a cover image and working table of contents (see the template files in `/templates`). The script dynamically fills these templates with data scraped from royalroads. Scraping starts with a specified starting chapter, after which the script tries to look for a link to the next chapter. In this manner all chapters are scraped and added to the epub untill there is no next chapter link, and we are done.

# Troubleshooting

Some epubs may give a DRM warning when you try to open them on an EPUB reader. Anyway, things that worked for me were:

- Change the epub slightly, such as remove the cover image with e.g. `Sigil` on pc, and reupload
- Let the epub start at a later chapter, such as chapter 2. Optionally in combination with removing the image.

I find it very curious that DRM would trigger for an EPUB such as this that is created "from scratch" with a self-made script. The only things I can think of are:

- The cover image has DRM encyrption
  - Leaving the image out or removing it from the epub seems to work sometimes, but not always.
- The text is "recognized" by the ereader as that it is DRM content
  - But how is this possible when my PC ánd ereader have no internet connection when uploading or reading the epub?
  - Maybe the ereader contains a set of keys for epubs that it knows are DRM content. This set o f keys is downloaded and stored on it when it has internet. The ereader "analyzes" (check first couple chapters?) a new epub, even without internet, against it known set of DRM content, and if no valid DRM license is found it is blocked.
- There is some code in one of the templates that says DRM validation is required for this book
  - Nothing I can find, especially as some epubs created with this script contain no DRM, and some do.
- The text scraped from RR is already DRM encrypted
  - This seems unlikely, as it is basic HTML.
