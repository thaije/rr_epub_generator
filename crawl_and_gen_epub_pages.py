from bs4 import BeautifulSoup
import requests
import os

base_url = "https://www.royalroad.com"
starting_url = "/fiction/8463/the-arcane-emperor/chapter/94620/chapter-1-new-beginnings"
output_folder = "output"
template_page_file_name = "template.html"


def read_in_template_page():
    text_file = open(template_page_file_name, "r")
    template_page = text_file.read()
    text_file.close()

    print(f"Read in template page {template_page_file_name}")
    return template_page


def get_chapter(url):
    if base_url not in url:
        url = base_url + url

    response = requests.get(url)
    html = response.content.decode()
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def get_next_chapter(chapter):

    # fetch next chapter url
    next_chapter_url = None  # TODO: get next chapter url from chapter

    for item in chapter.find_all(["a"], attrs={'class': 'btn-primary'}):
        if item.text == "Next Chapter":
            next_chapter_url = item['href']
            # print("Found next chapter with link", next_chapter_url)
            break

    if next_chapter_url is None:
        return False

    # fetch chapter if any found
    else:
        return get_chapter(next_chapter_url)


def get_content(chapter):
    # get the contents of this div
    result = chapter.find('div', attrs={'class': 'chapter-content'}).contents

    result_str = ""
    for line in result:
        result_str += str(line)

    # replace stuff that breaks epub pages
    result_str = result_str.replace("<hr>", "<hr/>")
    result_str = result_str.replace("<br>", "<br/>")

    return result_str


def get_title(chapter):
    result = chapter.find('h1')
    return result.text


def write_to_page(template_page, title, content):
    html_template = template_page

    html_template = html_template.replace("%title%", title)
    html_template = html_template.replace("%content%", content)

    path = output_folder + "/" + title.replace(" ", "_") + ".html"

    # Create the directory if not given
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    text_file = open(path, "w+")
    text_file.write(html_template)
    text_file.close()


# Defining main function
def main():
    # read in template for Epub pages
    template_page = read_in_template_page()

    print(f"Parsing chapters starting from {starting_url}")
    chapter_i = 0

    # parse the first chapter
    chapter = get_chapter(starting_url)
    while chapter:
        chapter_i += 1

        title = get_title(chapter)
        content = get_content(chapter)
        print(f"Parsed chapter {title}")

        write_to_page(template_page, title, content)

        chapter = get_next_chapter(chapter)

    print(f"Completed parsing {chapter_i} chapters")


if __name__ == "__main__":
    main()
