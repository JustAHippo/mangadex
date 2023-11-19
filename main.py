import os
import shutil
import zipfile

import requests

def get_title_info(title_id: str):
    requestURL = "https://api.mangadex.org/manga/{}".format(title_id)
    main_req = requests.get(requestURL)
    return main_req.json()
def retrieve_chapters(title_id: str, lang: str = "en", specified_volumes: list = []):
    limit = 500
    specific_volumes = specified_volumes != []
    requestURL = "https://api.mangadex.org/manga/{}/feed?limit={}".format(title_id, limit)
    main_req = requests.get(requestURL)
    response = main_req.json()["data"]
    print("Retrieving a total of: " + str(main_req.json()["total"]) + " chapters!")
    if main_req.json()["total"] > 500:
        print("More than 500! Retrieving more!")

        offset = 500
        recurringRequestURL = "https://api.mangadex.org/manga/{}/feed?limit=500&offset={}".format(title_id, offset)
        recurringResponse = requests.get(recurringRequestURL).json()["data"]
        response += recurringResponse
        while recurringResponse != []:
            offset += 500
            recurringRequestURL = "https://api.mangadex.org/manga/{}/feed?limit=500&offset={}".format(title_id, offset)
            recurringResponse = requests.get(recurringRequestURL).json()["data"]
            response += recurringResponse
            print("Retrieved next page! Offset of " + str(offset))
        print("Finished loop through of chapters with final offset of " + str(offset))

    wanted_chapters = []
    if specific_volumes:
        for part in response:
            if part["attributes"]["translatedLanguage"] == lang and part["attributes"]["pages"] != 0:
                for volume in specified_volumes:
                    if volume == part["attributes"]["volume"]:
                        wanted_chapters.append(part)

    else:
        for part in response:
            if part["attributes"]["translatedLanguage"] == lang and part["attributes"]["pages"] != 0:
                wanted_chapters.append(part)

    return wanted_chapters
def get_chapter_pages(chapter_id: str, data_saver: bool = False):
    requestURL = "https://api.mangadex.org/at-home/server/{}".format(chapter_id)
    main_req = requests.get(requestURL)
    response = main_req.json()
    image_urls = []
    url_prefix = ""
    if data_saver:
        image_urls = response["chapter"]["dataSaver"]
        url_prefix = "data-saver"
    else:
        image_urls = response["chapter"]["data"]
        url_prefix = "data"
    i = 0
    for image in image_urls:
        image_urls[i] = "{}/{}/{}/{}".format(response["baseUrl"], url_prefix, response["chapter"]["hash"], image)
        i += 1
    return image_urls
def download_chapter(image_urls: list, chapter, relative_path: str, data_saver: bool = False, make_cbz: bool = True):
    chapter_name = "{}  {}".format(chapter["attributes"]["chapter"], chapter["attributes"]["title"])
    chapter_name = chapter_name.replace(":", "")
    chapter_name = chapter_name.replace("?", "")
    chapter_name = chapter_name.replace(".", "")
    chapter_name = chapter_name.replace("/", "")
    if chapter["attributes"]["volume"]:
        volume_name = "Volume " + chapter["attributes"]["volume"]
    else:
        volume_name = "Volume None"
    file_extension = ""
    if data_saver:
        file_extension = ".jpg"
    else:
        file_extension = ".png"
    i = 1
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = ROOT_DIR.replace("\\", "/")
    chapter_dir = "{}/{}{}/{}/".format(ROOT_DIR, relative_path, volume_name, chapter_name)
    volume_dir = "{}/{}{}/".format(ROOT_DIR, relative_path, volume_name)
    cbz_path = '{}{}'.format(volume_dir, chapter_name)
    cbz_file = '{}{}.cbz'.format(volume_dir, chapter_name)
    if make_cbz:
        if os.path.isfile(cbz_file):
            print("CBZ Already exists for {}: {}!".format(volume_name, chapter_name))
            return
    if not os.path.exists(chapter_dir):
        print("Downloading "  +volume_name +" Chapter " + chapter_name)
        os.makedirs(chapter_dir)
        for url in image_urls:
            request_image = requests.get(url).content

            fileName = os.path.join(chapter_dir, "{}{}".format(i, file_extension))
            file = open(fileName, "wb")
            file.write(request_image)
            file.close()
            i += 1
    else:
        print(chapter_name + " Already downloaded folder!")
    if make_cbz:

        print("Making CBZ...")
        print(chapter_dir)
        #shutil.make_archive(cbz_path, 'zip', chapter_dir)
        with zipfile.ZipFile(cbz_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            zipdir(chapter_dir, zipf)
        #os.rename(cbz_path + ".zip", cbz_path + ".cbz")
            zipf.close()
        shutil.rmtree(chapter_dir)
def retrieve_series(title_id: str, language: str = "en", data_saver: bool = False, specified_volumes: list = [], make_cbz: bool = True):
    title_info = get_title_info(title_id)
    chapters = retrieve_chapters(title_id, "en", specified_volumes)
    title_name = title_info["data"]["attributes"]["title"]["en"] # Almost all titles only have an "en" variant, and the "altTitles" list is only occasionally available
    for chapter in chapters:
        page_urls = get_chapter_pages(chapter["id"], data_saver)
        download_chapter(page_urls, chapter, "output/{}/".format(title_name), data_saver, make_cbz)
def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file),
                       os.path.relpath(os.path.join(root, file),
                                       os.path.join(path, '..')))



#retrieve_series("ID(example has Link Click)", "LANG_ID", data_saver, ["Array of volume #s", "MUST BE STRINGS", "if empty array, downloads all"], make_cbz)
retrieve_series("72e51451-4d0c-4a3f-97ff-afb3f819fbfa", "en", False, [], True)
