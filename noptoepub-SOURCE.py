import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import turtle
from ebooklib import epub
from datetime import datetime, timezone
import time

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
    return None

def extract_article_body(response):
    soup = BeautifulSoup(response.text, "html.parser")

    name = soup.find("a", class_="subreddit-name", href=lambda h: h and h.startswith("/r/"))
    subreddit = name.get_text(strip=True) if name else "Unknown Subreddit"

    author_tag = soup.find("a", class_="author-name", href=lambda h: h and h.startswith("/user/"))
    author = author_tag.get_text(strip=True) if author_tag else "Unknown Author"


    h1 = soup.find("h1")
    title = h1.get_text(strip=True) if h1 else "Untitled"

    div = soup.find("div", attrs={"property": "schema:articleBody"})
    if not div:
        return "", subreddit, author, title

    html_lines = [f"<h1>{title}</h1>"]

    for child in div.children:
        if getattr(child, "name", None):
            html_lines.append(str(child))
        elif isinstance(child, str) and child.strip():
            html_lines.append(f"<p>{child.strip()}</p>")

    html = "\n".join(html_lines)
    return html, subreddit, author, title

start_url = turtle.textinput(
    "Enter Url",
    "Enter FULL reddit url of first chapter (eg https://www.reddit.com/r/HFY/comments/u19xpa/the_nature_of_predators/)"
)
if start_url == "":
    f.write("No URL entered\n")
    raise SystemExit

book_title = turtle.textinput(
    "Enter Title",
    "Enter title of the EPUB (If left blank the epub will be titled untitled.epub)"
)
if book_title == "":
    book_title = "untitled"
    f.write("Book title not entered, set to untitled\n")

book_cover = turtle.textinput(
    "Enter Cover Url",
    "Enter url of cover image (right click image -> copy image link) (If left blank cover will be blank)"
)
if book_cover == "":
    book_cover = "https://i.imgur.com/JegySXD.png"
    f.write("Book cover not entered, set to blank\n")

book = epub.EpubBook()
book.set_title(book_title)
book.set_language("en")
book.set_identifier(start_url)

data = requests.get(url=book_cover).content
g = open('cover.jpg','wb')
g.write(data)
g.close()

img = epub.EpubImage()
img.file_name = "images/pic.jpg"
img.media_type = "image/jpeg"
img.content = data
book.add_item(img)
book.set_cover("img.jpg", data)

nav_css = epub.EpubItem(
    uid="style_nav",
    file_name="style/nav.css",
    media_type="text/css",
    content="body { font-family: serif; margin: 5%; line-height: 1.6; }",
)
book.add_item(nav_css)

chapter_list = []
start_time = time.time()
iteration_count = 0

while start_url:
    iteration_count += 1
    response = requests.get(start_url, timeout=10)
    if response.status_code == 429:
        f.write("Too many requests, Please let me know if you get this error (my rate limiter messed up) and try again in ~5 minutes :<\n")
        break
    elif response.status_code != 200:
        f.write("Failed to retrieve page, Reddit is probably down right now, try again later :3\n")
        break

    html, subreddit, author, title = extract_article_body(response)

    ch = epub.EpubHtml(
        title=title,
        file_name=str(len(chapter_list)+1) + ".xhtml",
        lang="en"
    )
    ch.content = html or "<p>Empty chapter</p>"
    chapter_list.append(ch)

    start_url = find_next_link(response)

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

for ch in chapter_list:
    book.add_item(ch)

book.add_item(epub.EpubNav())
book.add_item(epub.EpubNcx())
book.toc = tuple(epub.Link(ch.file_name, ch.title, ch.file_name) for ch in chapter_list)
book.spine = ["nav"] + chapter_list

book.add_metadata("DC", "creator", author)
book.add_metadata("DC", "publisher", subreddit)

epub.write_epub(str(book_title) + ".epub", book)
f.write("EPUB created successfully\n")
f.close()