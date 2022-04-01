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

    print("Done writing epub")


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
    # chapters = [
    #     {'title': 'Chapter 1: New Beginnings', 'file_name': 'Chapter_1:_New_Beginnings.html'},
    #     {'title': "Chapter 2: I'm Sorry I Doubted you Grandfather!",
    #      'file_name': "Chapter_2:_I'm_Sorry_I_Doubted_you_Grandfather!.html"},
    #     {'title': 'Chapter 3: The Arcane Scholar', 'file_name': 'Chapter_3:_The_Arcane_Scholar.html'},
    #     {'title': 'Chapter 4: A Fairy and a Broken Seal', 'file_name': 'Chapter_4:_A_Fairy_and_a_Broken_Seal.html'},
    #     {'title': 'Chapter 5: Fae Contractor', 'file_name': 'Chapter_5:_Fae_Contractor.html'},
    #     {'title': 'Chapter 6: Run with the Wind!', 'file_name': 'Chapter_6:_Run_with_the_Wind!.html'},
    #     {'title': 'Chapter 7: Resistance', 'file_name': 'Chapter_7:_Resistance.html'},
    #     {'title': 'Chapter 8: The Arcane Elementalist', 'file_name': 'Chapter_8:_The_Arcane_Elementalist.html'},
    #     {'title': 'Chapter 9: Monster Hunters', 'file_name': 'Chapter_9:_Monster_Hunters.html'},
    #     {'title': "Chapter 10: Winter's Guardians", 'file_name': "Chapter_10:_Winter's_Guardians.html"},
    #     {'title': "Chapter 11: The Dungeon's Entrance", 'file_name': "Chapter_11:_The_Dungeon's_Entrance.html"},
    #     {'title': 'Chapter 12: The First Step', 'file_name': 'Chapter_12:_The_First_Step.html'},
    #     {'title': 'Chapter 13:  Fallen City of Nalmar', 'file_name': 'Chapter_13:__Fallen_City_of_Nalmar.html'},
    #     {'title': 'Chapter 14: A Change of Scenery ', 'file_name': 'Chapter_14:_A_Change_of_Scenery_.html'},
    #     {'title': 'Chapter 15: The Fog', 'file_name': 'Chapter_15:_The_Fog.html'},
    #     {'title': 'Chapter 16: An Unexpected Addition ', 'file_name': 'Chapter_16:_An_Unexpected_Addition_.html'},
    #     {'title': 'Chapter 17: Arcane Power', 'file_name': 'Chapter_17:_Arcane_Power.html'},
    #     {'title': 'Chapter 18: A Vanquishing Spear', 'file_name': 'Chapter_18:_A_Vanquishing_Spear.html'},
    #     {'title': 'Chapter 19: The Horde', 'file_name': 'Chapter_19:_The_Horde.html'},
    #     {'title': 'Chapter 20: Soar', 'file_name': 'Chapter_20:_Soar.html'},
    #     {'title': 'Chapter 21: Deliverance', 'file_name': 'Chapter_21:_Deliverance.html'},
    #     {'title': "Chapter 22: Wyvern's Roost", 'file_name': "Chapter_22:_Wyvern's_Roost.html"},
    #     {'title': 'Chapter 23: Domain', 'file_name': 'Chapter_23:_Domain.html'},
    #     {'title': 'Chapter 24: Rising Caverns and Falling Flames',
    #      'file_name': 'Chapter_24:_Rising_Caverns_and_Falling_Flames.html'},
    #     {'title': 'Chapter 25: Descent', 'file_name': 'Chapter_25:_Descent.html'},
    #     {'title': 'Chapter 26: The Return', 'file_name': 'Chapter_26:_The_Return.html'},
    #     {'title': 'Chapter 27: A Temporary Home', 'file_name': 'Chapter_27:_A_Temporary_Home.html'},
    #     {'title': 'Chapter 28: The Hunt', 'file_name': 'Chapter_28:_The_Hunt.html'},
    #     {'title': 'Chapter 29: Back to Where it All Began', 'file_name': 'Chapter_29:_Back_to_Where_it_All_Began.html'},
    #     {'title': 'Chapter 30: Standardization', 'file_name': 'Chapter_30:_Standardization.html'},
    #     {'title': 'Chapter 31: Final Preparations', 'file_name': 'Chapter_31:_Final_Preparations.html'},
    #     {'title': 'Chapter 32: Advancement ', 'file_name': 'Chapter_32:_Advancement_.html'},
    #     {'title': 'Chapter 33: Fruit of the World Tree', 'file_name': 'Chapter_33:_Fruit_of_the_World_Tree.html'},
    #     {'title': 'Chapter 34: A New Wind Blows. ', 'file_name': 'Chapter_34:_A_New_Wind_Blows._.html'},
    #     {'title': 'Chapter 35: The Low Road', 'file_name': 'Chapter_35:_The_Low_Road.html'},
    #     {'title': 'Chapter 36: Toward the Tower', 'file_name': 'Chapter_36:_Toward_the_Tower.html'},
    #     {'title': 'Chapter 37: A Familiar Sensation', 'file_name': 'Chapter_37:_A_Familiar_Sensation.html'},
    #     {'title': 'Chapter 38: The Mana-Well', 'file_name': 'Chapter_38:_The_Mana-Well.html'},
    #     {'title': 'Chapter 39: Voidwalker', 'file_name': 'Chapter_39:_Voidwalker.html'},
    #     {'title': 'Chapter 40: Maiden Elru', 'file_name': 'Chapter_40:_Maiden_Elru.html'},
    #     {'title': 'Chapter 41: A Trade', 'file_name': 'Chapter_41:_A_Trade.html'},
    #     {'title': "Chapter 42: A Ring's Value", 'file_name': "Chapter_42:_A_Ring's_Value.html"},
    #     {'title': 'Chapter 43: Flame-Touched', 'file_name': 'Chapter_43:_Flame-Touched.html'},
    #     {'title': 'Chapter 44: Of Mages and Arachne', 'file_name': 'Chapter_44:_Of_Mages_and_Arachne.html'},
    #     {'title': 'Chapter 45: A Message', 'file_name': 'Chapter_45:_A_Message.html'},
    #     {'title': 'Chapter 46: Arcane Presence', 'file_name': 'Chapter_46:_Arcane_Presence.html'},
    #     {'title': 'Chapter 47: Druidic Magic', 'file_name': 'Chapter_47:_Druidic_Magic.html'},
    #     {'title': 'Chapter 48: The Ice Wolf Queen', 'file_name': 'Chapter_48:_The_Ice_Wolf_Queen.html'},
    #     {'title': 'Chapter 49: Not Even a Footnote', 'file_name': 'Chapter_49:_Not_Even_a_Footnote.html'},
    #     {'title': 'Chapter 50: Arcane Invigoration', 'file_name': 'Chapter_50:_Arcane_Invigoration.html'},
    #     {'title': 'Chapter 51: Devil King Agmar', 'file_name': 'Chapter_51:_Devil_King_Agmar.html'},
    #     {'title': 'Chapter 52: An Unexpected Destination ', 'file_name': 'Chapter_52:_An_Unexpected_Destination_.html'},
    #     {'title': 'Chapter 53: A New Arrival', 'file_name': 'Chapter_53:_A_New_Arrival.html'},
    #     {'title': 'Chapter 54: The Arcane Order', 'file_name': 'Chapter_54:_The_Arcane_Order.html'},
    #     {'title': 'Chapter 55: Frozen Sun', 'file_name': 'Chapter_55:_Frozen_Sun.html'},
    #     {'title': 'Chapter 56: Tiers of Magic', 'file_name': 'Chapter_56:_Tiers_of_Magic.html'},
    #     {'title': 'Chapter 57: The Ball', 'file_name': 'Chapter_57:_The_Ball.html'},
    #     {'title': 'Chapter 58: The Soul', 'file_name': 'Chapter_58:_The_Soul.html'},
    #     {'title': 'Chapter 59: Call of the Void', 'file_name': 'Chapter_59:_Call_of_the_Void.html'},
    #     {'title': 'Chapter 60: Abyssal Plane', 'file_name': 'Chapter_60:_Abyssal_Plane.html'},
    #     {'title': 'Chapter 61: Creeping Darkness', 'file_name': 'Chapter_61:_Creeping_Darkness.html'},
    #     {'title': 'Chapter 62: The Mind', 'file_name': 'Chapter_62:_The_Mind.html'},
    #     {'title': "Chapter 63: A Serpent's Cry and A Dragon's Help",
    #      'file_name': "Chapter_63:_A_Serpent's_Cry_and_A_Dragon's_Help.html"},
    #     {'title': 'Chapter 64: Lords of the Void', 'file_name': 'Chapter_64:_Lords_of_the_Void.html'},
    #     {'title': 'Chapter 65: Plunging into Water', 'file_name': 'Chapter_65:_Plunging_into_Water.html'},
    #     {'title': 'Chapter 66: The Second Trial', 'file_name': 'Chapter_66:_The_Second_Trial.html'},
    #     {'title': 'Chapter 67: Abyssal Elf', 'file_name': 'Chapter_67:_Abyssal_Elf.html'},
    #     {'title': 'Chapter 68: A Difference of Time', 'file_name': 'Chapter_68:_A_Difference_of_Time.html'},
    #     {'title': "Chapter 69: Death's Thief", 'file_name': "Chapter_69:_Death's_Thief.html"},
    #     {'title': 'Chapter 70: The Memories of a Soul', 'file_name': 'Chapter_70:_The_Memories_of_a_Soul.html'},
    #     {'title': 'Chapter 71: Arcane Revelation', 'file_name': 'Chapter_71:_Arcane_Revelation.html'},
    #     {'title': 'Chapter 72: Another gift from the Divine',
    #      'file_name': 'Chapter_72:_Another_gift_from_the_Divine.html'},
    #     {'title': 'Chapter 73: Home', 'file_name': 'Chapter_73:_Home.html'},
    #     {'title': 'Chapter 74: To New Horizons', 'file_name': 'Chapter_74:_To_New_Horizons.html'},
    #     {'title': 'Chapter 75: Magus of Cursed Lightning', 'file_name': 'Chapter_75:_Magus_of_Cursed_Lightning.html'},
    #     {'title': 'Chapter 76: Of Enchantments and Dragons',
    #      'file_name': 'Chapter_76:_Of_Enchantments_and_Dragons.html'},
    #     {'title': 'Chapter 77: White Void', 'file_name': 'Chapter_77:_White_Void.html'},
    #     {'title': 'Chapter 78: A Broken Soul', 'file_name': 'Chapter_78:_A_Broken_Soul.html'},
    #     {'title': 'Chapter 79: Sacrilege', 'file_name': 'Chapter_79:_Sacrilege.html'},
    #     {'title': 'Chapter 80: Gateway', 'file_name': 'Chapter_80:_Gateway.html'},
    #     {'title': 'Chapter 81: Void-Step', 'file_name': 'Chapter_81:_Void-Step.html'},
    #     {'title': 'Chapter 82: Bard of the Moonlight', 'file_name': 'Chapter_82:_Bard_of_the_Moonlight.html'},
    #     {'title': 'Chapter 83: Arcanum', 'file_name': 'Chapter_83:_Arcanum.html'},
    #     {'title': 'Chapter 84: Threads of Aura', 'file_name': 'Chapter_84:_Threads_of_Aura.html'},
    #     {'title': 'Chapter 85: The Wolf King', 'file_name': 'Chapter_85:_The_Wolf_King.html'},
    #     {'title': 'Chapter 86: Changing of the Guard', 'file_name': 'Chapter_86:_Changing_of_the_Guard.html'},
    #     {'title': 'Chapter 87: Moonlighting', 'file_name': 'Chapter_87:_Moonlighting.html'},
    #     {'title': 'Chapter 88: Neutral City', 'file_name': 'Chapter_88:_Neutral_City.html'},
    #     {'title': 'Chapter 89: Blood on the Walls', 'file_name': 'Chapter_89:_Blood_on_the_Walls.html'},
    #     {'title': 'Chapter 90: Creature of Shadow', 'file_name': 'Chapter_90:_Creature_of_Shadow.html'},
    #     {'title': 'Chapter 91: Manipulator of Reality ', 'file_name': 'Chapter_91:_Manipulator_of_Reality_.html'},
    #     {'title': 'Chapter 92: First Impressions', 'file_name': 'Chapter_92:_First_Impressions.html'},
    #     {'title': 'Chapter 93: Elemental Awakening ', 'file_name': 'Chapter_93:_Elemental_Awakening_.html'},
    #     {'title': 'Chapter 94: Of Arcane and Frost', 'file_name': 'Chapter_94:_Of_Arcane_and_Frost.html'},
    #     {'title': 'Chapter 95: Avatar', 'file_name': 'Chapter_95:_Avatar.html'},
    #     {'title': 'Chapter 96: Weaknesses', 'file_name': 'Chapter_96:_Weaknesses.html'},
    #     {'title': 'Chapter 97: To the Land of Demons', 'file_name': 'Chapter_97:_To_the_Land_of_Demons.html'},
    #     {'title': 'Chapter 98: Demonic Dungeon', 'file_name': 'Chapter_98:_Demonic_Dungeon.html'},
    #     {'title': 'Chapter 99: A Split', 'file_name': 'Chapter_99:_A_Split.html'},
    #     {'title': 'Chapter 100: Destination', 'file_name': 'Chapter_100:_Destination.html'},
    #     {'title': 'Chapter 101: Opening the [Sleep Learning] Space',
    #      'file_name': 'Chapter_101:_Opening_the_[Sleep_Learning]_Space.html'},
    #     {'title': 'Chapter 102: A World of Mana', 'file_name': 'Chapter_102:_A_World_of_Mana.html'},
    #     {'title': 'Chapter 103: Frontline', 'file_name': 'Chapter_103:_Frontline.html'},
    #     {'title': 'Chapter 104: Reunion', 'file_name': 'Chapter_104:_Reunion.html'},
    #     {'title': 'Chapter 105: Matters of the Soul', 'file_name': 'Chapter_105:_Matters_of_the_Soul.html'},
    #     {'title': 'Chapter 106: The Strength of the System',
    #      'file_name': 'Chapter_106:_The_Strength_of_the_System.html'},
    #     {'title': 'Chapter 107: Balance', 'file_name': 'Chapter_107:_Balance.html'},
    #     {'title': 'Chapter 108: Ready for War', 'file_name': 'Chapter_108:_Ready_for_War.html'},
    #     {'title': 'Chapter 109: Borrowing Natural Laws', 'file_name': 'Chapter_109:_Borrowing_Natural_Laws.html'},
    #     {'title': 'Chapter 110:  A New Energy', 'file_name': 'Chapter_110:__A_New_Energy.html'},
    #     {'title': 'Chapter 111: Blade of the Void', 'file_name': 'Chapter_111:_Blade_of_the_Void.html'},
    #     {'title': 'Chapter 112: Void-Being', 'file_name': 'Chapter_112:_Void-Being.html'},
    #     {'title': 'Chapter 113: Auction', 'file_name': 'Chapter_113:_Auction.html'},
    #     {'title': 'Chapter 114: An Unassuming Chosen', 'file_name': 'Chapter_114:_An_Unassuming_Chosen.html'},
    #     {'title': 'Chapter 115: Fight or Flight', 'file_name': 'Chapter_115:_Fight_or_Flight.html'},
    #     {'title': 'Chapter 116: Receiving the System', 'file_name': 'Chapter_116:_Receiving_the_System.html'},
    #     {'title': 'Chapter 117: Family Gathering', 'file_name': 'Chapter_117:_Family_Gathering.html'},
    #     {'title': 'Chapter 118: Ancient Aspects', 'file_name': 'Chapter_118:_Ancient_Aspects.html'},
    #     {'title': 'Chapter 119: Changing', 'file_name': 'Chapter_119:_Changing.html'},
    #     {'title': 'Chapter 120: Seeking New Dungeons', 'file_name': 'Chapter_120:_Seeking_New_Dungeons.html'},
    #     {'title': 'Chapter 121: Passives', 'file_name': 'Chapter_121:_Passives.html'},
    #     {'title': 'Chapter 122: Arcane Domain', 'file_name': 'Chapter_122:_Arcane_Domain.html'},
    #     {'title': 'Chapter 123: Black-Fire', 'file_name': 'Chapter_123:_Black-Fire.html'},
    #     {'title': 'Chapter 124: A Ghost in the Snow', 'file_name': 'Chapter_124:_A_Ghost_in_the_Snow.html'},
    #     {'title': 'Chapter 125: Remnants of the Northern Empire',
    #      'file_name': 'Chapter_125:_Remnants_of_the_Northern_Empire.html'},
    #     {'title': 'Chapter 126: Remnants of the Northern Empire(2)',
    #      'file_name': 'Chapter_126:_Remnants_of_the_Northern_Empire(2).html'},
    #     {'title': 'Chapter 127:  Preparing for the Dungeon',
    #      'file_name': 'Chapter_127:__Preparing_for_the_Dungeon.html'},
    #     {'title': 'Chapter 128: A Living Poison', 'file_name': 'Chapter_128:_A_Living_Poison.html'},
    #     {'title': 'Chapter 129: Godling', 'file_name': 'Chapter_129:_Godling.html'},
    #     {'title': 'Chapter 130: Celebration', 'file_name': 'Chapter_130:_Celebration.html'},
    #     {'title': 'Chapter 131: Mage-Fist', 'file_name': 'Chapter_131:_Mage-Fist.html'},
    #     {'title': 'Chapter 132: Coronation ', 'file_name': 'Chapter_132:_Coronation_.html'},
    #     {'title': 'Chapter 133: Seeking a Seer', 'file_name': 'Chapter_133:_Seeking_a_Seer.html'},
    #     {'title': 'Chapter 134: Manipulating the Body', 'file_name': 'Chapter_134:_Manipulating_the_Body.html'},
    #     {'title': 'Chapter 135: Gold to Crimson', 'file_name': 'Chapter_135:_Gold_to_Crimson.html'},
    #     {'title': "Chapter 136: Sarah's Trial", 'file_name': "Chapter_136:_Sarah's_Trial.html"},
    #     {'title': 'Chapter 137: Let the Hunt Begin', 'file_name': 'Chapter_137:_Let_the_Hunt_Begin.html'},
    #     {'title': 'Chapter 138: Collecting', 'file_name': 'Chapter_138:_Collecting.html'},
    #     {'title': 'Chapter 139: Leaderboard', 'file_name': 'Chapter_139:_Leaderboard.html'},
    #     {'title': 'Chapter 140: Arcane and Void', 'file_name': 'Chapter_140:_Arcane_and_Void.html'},
    #     {'title': 'Chapter 141: Fighting for First', 'file_name': 'Chapter_141:_Fighting_for_First.html'},
    #     {'title': 'Chapter 142: Transformation', 'file_name': 'Chapter_142:_Transformation.html'},
    #     {'title': 'Chapter 143: The End of the First Stage',
    #      'file_name': 'Chapter_143:_The_End_of_the_First_Stage.html'},
    #     {'title': 'Chapter 144: The Second Stage', 'file_name': 'Chapter_144:_The_Second_Stage.html'},
    #     {'title': 'Chapter 145: Attrition', 'file_name': 'Chapter_145:_Attrition.html'},
    #     {'title': 'Chapter 146: Regeneration ', 'file_name': 'Chapter_146:_Regeneration_.html'},
    #     {'title': 'Chapter 147: Core', 'file_name': 'Chapter_147:_Core.html'},
    #     {'title': 'Chapter 148: A Land of Frost', 'file_name': 'Chapter_148:_A_Land_of_Frost.html'},
    #     {'title': 'Chapter 149: Soul Resilience', 'file_name': 'Chapter_149:_Soul_Resilience.html'},
    #     {'title': 'Chapter 150: Rest Area', 'file_name': 'Chapter_150:_Rest_Area.html'},
    #     {'title': 'Chapter 151: Order of the Elements', 'file_name': 'Chapter_151:_Order_of_the_Elements.html'},
    #     {'title': 'Chapter 152: Failed Creation', 'file_name': 'Chapter_152:_Failed_Creation.html'},
    #     {'title': 'Chapter 153: Drifting Isle', 'file_name': 'Chapter_153:_Drifting_Isle.html'},
    #     {'title': 'Chapter 154: Round 1', 'file_name': 'Chapter_154:_Round_1.html'},
    #     {'title': 'Chapter 155: Round Robin', 'file_name': 'Chapter_155:_Round_Robin.html'},
    #     {'title': 'Chapter 156: Visiting', 'file_name': 'Chapter_156:_Visiting.html'},
    #     {'title': 'Chapter 157: Final Round', 'file_name': 'Chapter_157:_Final_Round.html'},
    #     {'title': 'Chapter 158: A Life for a Life', 'file_name': 'Chapter_158:_A_Life_for_a_Life.html'},
    #     {'title': 'Chapter 159: A Pairing of Arcane and Void',
    #      'file_name': 'Chapter_159:_A_Pairing_of_Arcane_and_Void.html'},
    #     {'title': 'Chapter 160: The Last Fight', 'file_name': 'Chapter_160:_The_Last_Fight.html'},
    #     {'title': 'Chapter 161: Final Reward', 'file_name': 'Chapter_161:_Final_Reward.html'},
    #     {'title': 'Chapter 162: Preparation for War ', 'file_name': 'Chapter_162:_Preparation_for_War_.html'},
    #     {'title': 'Chapter 163: An Empty Field of Grass', 'file_name': 'Chapter_163:_An_Empty_Field_of_Grass.html'},
    #     {'title': 'Chapter 164: Flee', 'file_name': 'Chapter_164:_Flee.html'},
    #     {'title': 'Chapter 165: A Light from the Moon', 'file_name': 'Chapter_165:_A_Light_from_the_Moon.html'},
    #     {'title': 'Chapter 166: The City of Wealth', 'file_name': 'Chapter_166:_The_City_of_Wealth.html'},
    #     {'title': 'Chapter 167: Copying Memories', 'file_name': 'Chapter_167:_Copying_Memories.html'},
    #     {'title': 'Chapter 168: A Changing of Soul', 'file_name': 'Chapter_168:_A_Changing_of_Soul.html'},
    #     {'title': 'Chapter 169: A Third Avatar', 'file_name': 'Chapter_169:_A_Third_Avatar.html'},
    #     {'title': 'Chapter 170: A Badge and a Coin', 'file_name': 'Chapter_170:_A_Badge_and_a_Coin.html'},
    #     {'title': 'Chapter 171: Informant', 'file_name': 'Chapter_171:_Informant.html'},
    #     {'title': 'Chapter 172: Transportation', 'file_name': 'Chapter_172:_Transportation.html'},
    #     {'title': 'Chapter 173: Meeting the Invasion', 'file_name': 'Chapter_173:_Meeting_the_Invasion.html'},
    #     {'title': 'Chapter 174: A New Enemy', 'file_name': 'Chapter_174:_A_New_Enemy.html'},
    #     {'title': 'Chapter 175: Repository of Souls', 'file_name': 'Chapter_175:_Repository_of_Souls.html'},
    #     {'title': 'Chapter 176: The Four Towers', 'file_name': 'Chapter_176:_The_Four_Towers.html'},
    #     {'title': 'Chapter 177: A New Guild', 'file_name': 'Chapter_177:_A_New_Guild.html'},
    #     {'title': 'Chapter 178: Rushing Forward', 'file_name': 'Chapter_178:_Rushing_Forward.html'},
    #     {'title': 'Chapter 179: Runes of Mana', 'file_name': 'Chapter_179:_Runes_of_Mana.html'},
    #     {'title': "Chapter 180: The Worth of a Mage's Life",
    #      'file_name': "Chapter_180:_The_Worth_of_a_Mage's_Life.html"},
    #     {'title': 'Chapter 181: Of Gods and Empires', 'file_name': 'Chapter_181:_Of_Gods_and_Empires.html'},
    #     {'title': 'Chapter 182: New faces, Old Enemies', 'file_name': 'Chapter_182:_New_faces,_Old_Enemies.html'},
    #     {'title': 'Chapter 183: An Invitation of the Elements',
    #      'file_name': 'Chapter_183:_An_Invitation_of_the_Elements.html'},
    #     {'title': 'Chapter 184: The Second Tower of Conquest',
    #      'file_name': 'Chapter_184:_The_Second_Tower_of_Conquest.html'},
    #     {'title': 'Chapter 185: Soul Assault', 'file_name': 'Chapter_185:_Soul_Assault.html'},
    #     {'title': 'Chapter 186: A Difference in Quality', 'file_name': 'Chapter_186:_A_Difference_in_Quality.html'},
    #     {'title': 'Chapter 187: Swift Vengeance', 'file_name': 'Chapter_187:_Swift_Vengeance.html'},
    #     {'title': 'Chapter 188: Violet Death', 'file_name': 'Chapter_188:_Violet_Death.html'},
    #     {'title': 'Chapter 189: A Quick Escape', 'file_name': 'Chapter_189:_A_Quick_Escape.html'},
    #     {'title': 'Chapter 190: Uri', 'file_name': 'Chapter_190:_Uri.html'},
    #     {'title': 'Chapter 191: Weak Training', 'file_name': 'Chapter_191:_Weak_Training.html'},
    #     {'title': 'Chapter 192: Stirring the Pot', 'file_name': 'Chapter_192:_Stirring_the_Pot.html'},
    #     {'title': 'Chapter 193: Gilded Feathers', 'file_name': 'Chapter_193:_Gilded_Feathers.html'}]

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
