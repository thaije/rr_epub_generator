from bs4 import BeautifulSoup
import requests
import os
import zipfile
import warnings
import shutil

base_url = "https://www.royalroad.com"
starting_url = "/fiction/8463/the-arcane-emperor/chapter/94620/chapter-1-new-beginnings"
book_name = "The Arcane Emperor"


def read_in_page(file_name):
    text_file = open(file_name, "r")
    content = text_file.read()
    text_file.close()

    # print(f"Read in template {file_name}")
    return content


def get_cover():
    html = get_chapter(base_url + starting_url)

    # return "", "png"

    # get the cover url from the link
    img_link = html.find('img', attrs={'class': 'img-offset'})['src'].lower()

    img_name = img_link.split("/")[-1]
    file_extension = img_name.split(".")[-1]

    if file_extension not in ["jpg", "jpeg", "png"]:
        warnings.warn("Cover image is not a PNG or JPG, so skipping adding the cover image")
        return "", "png"

    if file_extension == "jpg":
        file_extension = "jpeg"

    # download the image
    img_data = requests.get(img_link).content

    print("Downloaded cover")

    return img_data, file_extension


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


def write_to_chapter(template_page, title, content):
    html_template = template_page
    output_folder = "output"

    html_template = html_template.replace("%title%", title)
    html_template = html_template.replace("%content%", content)

    file_title = title.replace(" ", "_") + ".html"
    path = output_folder + "/" + file_title

    # Create the directory if not given
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    text_file = open(path, "w+")
    text_file.write(html_template)
    text_file.close()

    return file_title


def write_page(path, content):
    # Create the directory if not given
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    text_file = open(path, "w+")
    text_file.write(content)
    text_file.close()

    # print("Created file ", path)


def crawl_chapters():
    """ Crawls all chapters from RR and puts them in a HTML format according to the template """
    chapter_list = []

    chapter_template = read_in_page("templates/chapter_template.html")

    print(f"Parsing chapters starting from {starting_url}")
    chapter_i = 0

    # parse the first chapter
    chapter = get_chapter(starting_url)
    while chapter:
        chapter_i += 1

        title = get_title(chapter)
        content = get_content(chapter)
        print(f"Parsed chapter {chapter_i}")

        file_name = write_to_chapter(chapter_template, title, content)

        chapter_list.append({"title": title, "file_name": file_name})

        chapter = get_next_chapter(chapter)

    print(f"Completed parsing {chapter_i} chapters")

    return chapter_list


def create_content_file(chapters, img_file_extension):
    """ Create a content file so our epub reader can find our content """
    templ = read_in_page("templates/content_template.opf")

    chapter_manifest_items = []
    chapter_toc_items = []

    # create some content file stuff for each chapter
    for i, chapter in enumerate(chapters):
        # remove special characters from the title
        f_name = chapter['file_name']  # .replace(":")
        manifest_item = f'<item id="file_{i}" href="Text/{f_name}" media-type="application/xhtml+xml"/>'
        chapter_manifest_items.append(manifest_item)

        toc_item = f'<itemref idref="file_{i}"/>'
        chapter_toc_items.append(toc_item)

    # replace the placeholders in the template file with the real data
    templ = templ.replace("%title%", book_name)
    templ = templ.replace("%img_file_extension%", img_file_extension)
    templ = templ.replace("%chapter_manifest_items%", '\n'.join(chapter_manifest_items))
    templ = templ.replace("%chapter_toc_items%", '\n'.join(chapter_toc_items))

    write_page("output/content.opf", templ)

    print("Written cover file")


def create_toc_file(chapters):
    """ Create a table of contents to aid users in navigating their book while reading """
    templ = read_in_page("templates/toc_template.ncx")

    navpoints = []

    # create a navpoint for each chapter
    for i, chapter in enumerate(chapters):
        nav_item = f'<navPoint id="navPoint-{i+2}" playOrder="{i+2}"><navLabel><text>{chapter["title"]}</text></navLabel><content src="Text/{chapter["file_name"]}"/></navPoint>'
        navpoints.append(nav_item)

    # replace the placeholders in the template file with the real data
    templ = templ.replace("%title%", book_name)
    templ = templ.replace("%navpoints%", '\n'.join(navpoints))

    write_page("output/toc.ncx", templ)

    print("Written TOC")


def create_cover_file(chapters, cover_img_f_extension):
    """ create a file for holding the cover image """
    templ = read_in_page("templates/cover_template.xhtml")

    templ = templ.replace("%img_file_extension%", cover_img_f_extension)

    write_page("output/cover.xhtml", templ)

    print("Written cover file")


def write_to_epub(chapters, cover_img_data, cover_img_f_extension):
    epub = zipfile.ZipFile(f'{book_name}.epub', 'w')

    # read in our created pages
    toc = read_in_page('output/toc.ncx')
    content = read_in_page('output/content.opf')
    cover = read_in_page('output/cover.xhtml')
    container = read_in_page('templates/container_template.xml')

    # The first file must be named "mimetype"
    epub.writestr("mimetype", "application/epub+zip")

    # We need an index file, that lists all other HTML files
    # This index file itself is referenced in the META_INF/container.xml
    # file
    epub.writestr("META-INF/container.xml", container)

    # write them to the epub zip
    epub.writestr('OEBPS/toc.ncx', toc)
    epub.writestr('OEBPS/content.opf', content)
    epub.writestr('OEBPS/Text/cover.xhtml', cover)
    epub.writestr(f'OEBPS/Images/cover.{cover_img_f_extension}', cover_img_data)

    # write all chapters to the epub zip
    for chapter in chapters:
        chapter_content = read_in_page(f'output/{chapter["file_name"]}')
        epub.writestr(f'OEBPS/Text/{chapter["file_name"]}', chapter_content)

    print(f"Epub complete! See '{book_name}.epub'")


def cleanup():
    shutil.rmtree("output")
    print("Removed temporary files")


def main():
    print("Making an epub for ")
    print("~" * (len(book_name) + 5))
    print(" " + book_name)
    print("~" * (len(book_name) + 5))

    # crawl chapters from RR and put them in html pages
    chapters = crawl_chapters()

    # get the image cover
    cover_img_data, cover_img_f_extension = get_cover()

    # create some epub files
    create_content_file(chapters, cover_img_f_extension)
    create_toc_file(chapters)
    create_cover_file(chapters, cover_img_f_extension)

    # write all data to the epub
    write_to_epub(chapters, cover_img_data, cover_img_f_extension)

    # remove temp files
    cleanup()


if __name__ == "__main__":
    main()
