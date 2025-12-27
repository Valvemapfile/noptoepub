import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import turtle
from ebooklib import epub
import time
import sys

f = open("log.txt", "w")


screen = turtle.Screen()
screen.bgpic("bg.png")
screen.setup(width=800, height=600)
screen.title("Window will close once program is finished")

def find_next_link(response):

    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a"):
        if a.get_text(strip=True).lower() == "next":
            href = a.get("href")
            if href:
                return urljoin(response.url, href)
            else:
                return None

    return None

def extract_article_body(response):
    soup = BeautifulSoup(response.text, "html.parser")

    div = soup.find("div", attrs={"property": "schema:articleBody"})

    if not div:
        f.write("Target div not found\n")
        return "", ""

    html_lines = []
    text_lines = []

    for child in div.children:
        # Skip whitespace
        if getattr(child, "name", None) is None:
            continue

        # If it's already a paragraph or block, keep it
        if child.name in ("p", "blockquote", "ul", "ol"):
            html = str(child)
            text = child.get_text(strip=True)

        # Otherwise wrap it
        else:
            html = f"<p>{child.decode_contents()}</p>"
            text = child.get_text(strip=True)

        html_lines.append(html)
        text_lines.append(text)

    return "\n".join(text_lines), "\n".join(html_lines)

start_url = turtle.textinput("Enter Url", "Enter FULL reddit url of first chapter (eg https://www.reddit.com/r/HFY/comments/u19xpa/the_nature_of_predators/)")
if start_url == "":
    f.write("No URL entered\n")
book = epub.EpubBook()
book_title = turtle.textinput("Enter Title", "Enter title of the EPUB (If left blank the epub will be titled untitled.epub)")
if book_title == "":
    book_title = "untitled"
    f.write("Book title not entered, set to untitled\n")
book.set_title(book_title)
book.set_language("en")
book_cover = turtle.textinput("Enter Cover Url", "Enter url of cover image (right click image -> copy image link) (If left blank cover will be blank)")
if book_cover == "":
    book_cover = "https://i.imgur.com/JegySXD.png"
    f.write("Book cover not entered, set to blank\n")

data = requests.get(url=book_cover).content
g = open('cover.jpg','wb')
g.write(data)
g.close()


img = epub.EpubImage()
img.file_name = "images/pic.jpg"
img.media_type = "image/jpeg"
img.content = data


nav_css = epub.EpubItem(
    uid="style_nav",
    file_name="style/nav.css",
    media_type="text/css",
    content="body { font-family: serif; margin: 5%; line-height: 1.6; }",
)

chapter_list = []
start_time = time.time()
iteration_count = 0

for i in range(1, 99999):
    iteration_count += 1
    response = requests.get(start_url, timeout=10)
    if response.status_code == 429:
        f.write("Too many requests, Please let me know if you get this error (my rate limiter messed up) and try again in ~5 minutes :<\n")
        break
    elif response.status_code != 200:
        f.write("Failed to retrieve page, Reddit is probably down right now, try again later :3\n")
        break
    text, html = extract_article_body(response)
    i = epub.EpubHtml(title="Chapter " + str(i), file_name=str(i) + ".xhtml", lang="en")
    i.content = html
    chapter_list.append(i)
    start_url = find_next_link(response)
    if time.time() - start_time > 60 == 0:
        iteration_count = 0
        start_time = time.time()
    if iteration_count == 99:
        time.sleep(60 - (time.time() - start_time))
        iteration_count = 0
        start_time = time.time()
    if start_url:
        f.write("Next link found\n")
    else:
        f.write("Next link not found\n")
        break
    screen.update()

for i in range(len(chapter_list)):
    book.add_item(chapter_list[i])
book.add_item(img)
book.add_item(nav_css)
book.set_cover("img.jpg", open('cover.jpg', 'rb').read())

book.toc = tuple(epub.Link(chapter_list[i].file_name, chapter_list[i].title, chapter_list[i].file_name) for i in range(len(chapter_list)))

for i in range(len(chapter_list)):
    book.spine.append(chapter_list[i])


epub.write_epub(str(book_title) + ".epub", book)
f.write("EPUB created successfully\n")
f.close()