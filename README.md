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
