base_link = ""

if base_link == "":
    base_link = input("base_link seems to not be hardcoded. Please enter it (program will most likely error if incorrect): ")
    base_link = base_link.lstrip("https://").rstrip("/")

import os
import subprocess
import sys
import pkg_resources
import random
import time
import threading

#make sure additional packages are installed
required = {'urllib3', 'requests', 'beautifulsoup4', 'bs4', 'lxml'}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed
if missing:
    python = sys.executable
    subprocess.check_call([python, '-m', 'pip', 'install', *missing], stdout=subprocess.DEVNULL)

from bs4 import BeautifulSoup
import urllib.request
import requests

def download_post():
    global completed_downloads#
    global repeats
    #generating post index
    if direction == "r":
        post_index = total_posts.pop(random.randint(0, len(total_posts)-1))
    elif direction == "n":
        post_index = total_posts.pop(0)
    else:
        post_index = total_posts.pop(len(total_posts)-1)
    #getting the closest multiple of 42 to the post index
    closest_42_to_index = int((post_index-1) / 42) * 42

    #making page_link go to the page the post_index post is on
    page_link = "https://" + base_link + "/index.php?page=post&s=list&tags=" + tags + taglist + "+&pid=" + str(closest_42_to_index)

    while True:
        #getting html once again
        source = requests.get(page_link, headers=headers).text
        soup = BeautifulSoup(source, 'lxml')
        #indexing all the post ids on the page
        res = soup.findAll("span", {"class" : "thumb"})
        id_list = []
        for r in res:
            id_list.append(str(r['id'])[1:])
        if len(id_list) > 0:
            break

    #making link to post with id
    post_id = id_list[post_index - closest_42_to_index - 1]
    post_link = "https://" + base_link + "/index.php?page=post&s=view&id=" + post_id
    
    while True:
        try:
            #html, again
            source = requests.get(post_link, headers=headers).text
            soup = BeautifulSoup(source, 'lxml')
            #getting link to the source image
            res = soup.find("div", {"class":"link-list"}).contents[3].contents
            break
        except:
            pass
    k = 1
    while True:
        image_link = res[k].contents[1]["href"]
        if image_link != "#":
            break
        k += 2

    #getting file ending index
    j = len(image_link) - image_link.rfind(".")

    filename = f"{tags}/{tags} [{post_id}]{image_link[-j:image_link.rfind('?')]}"
    #skipping if the file has already been downloaded previously
    if os.path.exists(filename):
        if stop_on_repeat:
            repeats = completed_downloads
            return
        #if it is set to download everything, but one post has already been downloaded, decrease amount to download by 1
        #otherwise pick another post instead (don't mark this as a succesful download by incrementing i)
        if repeats - completed_downloads - 1 == len(total_posts):
            repeats -= 1
        return
    
    if not os.path.exists(tags):
        os.mkdir(tags)

    try:
        #downloading the image/video
        r = urllib.request.urlopen(image_link)
        with open(filename, "wb") as file:
            file.write(r.read())
    #in case of 404 not found
    except Exception:
        #attempt to get link through img src
        image_link = None
        res = soup.find("img", {"id":"image"})
        if res != None:
            image_link = res['src']
        else:
            res = soup.find("video", {"id":"gelcomVideoPlayer"})
            if res != None:
                image_link = res.contents[1]['src']

        if image_link != None:
            j = len(image_link) - image_link.rfind(".")
            filename = f"{tags}/{tags} [{post_id}]{image_link[-j:image_link.rfind('?')]}"
            
            r = urllib.request.urlopen(image_link)
        else:
            #if it is set to download everything, but one post can't be found, decrease amount to download by 1
            if repeats - completed_downloads - 1 == len(total_posts):
                repeats -= 1
            return
        
        with open(filename, "wb") as file:
            file.write(r.read())

    completed_downloads += 1

if len(sys.argv) > 1:
    print(f"Changing directory to {sys.argv[1]}")
    os.chdir(sys.argv[1])
else:
    print(f"No directory provided as argument, defaulting to {os.getcwd()}")
#setting user agent to make captcha ignore us
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

#adding tags from pre-defined list, if it exists
taglist = ""
taglist_file = ""
if os.path.exists("taglist.txt"):
    taglist_file = "taglist.txt"
elif os.path.exists(".taglist.txt"):
    taglist_file = ".taglist.txt"
if taglist_file != "":
    print(f"Found {taglist_file}, adding to tags.")
    with open(taglist_file, "r") as f:
        for line in f:
            taglist += "+" + line.rstrip("\n")
else:
    print("'taglist.txt' not found, consider creating it to make a blacklist")

tags = input("Enter tags (seperate tags with spaces): ")

stop_on_repeat = False
direction = input("Would you like to download randomly, newest first, or oldest first? [R/n/o] ").lower()
if direction != "n" and direction != "o":
    direction = "r"
    repeats = int(input("How many results would you like to download? (-1 for max) "))
else:
    repeats = int(input("How many results would you like to download? (-1 for downloading until a post is hit that has already been downloaded) "))
    if repeats == -1:
        stop_on_repeat = True

#making link to page one of results
page_link = "https://" + base_link + "/index.php?page=post&s=list&tags=" + tags + taglist + "+&pid=0"
#getting html of page one
source = requests.get(page_link, headers=headers).text
soup = BeautifulSoup(source, 'lxml')
#finding button that leads to the last page
res = soup.find("a", {"alt" : "last page"})
#total_posts is set to the url of last page button
if res != None:
    total_posts = res['href']
else:
    total_posts = page_link

#only keeping the number from the url (the urls only count to the closest multiple of 42 and not the actual number of posts)
total_posts = total_posts[total_posts.rfind("&pid") + 5:]
#making page_link go to last instead of first page
page_link = page_link[:-1] + total_posts
#getting html
source = requests.get(page_link, headers=headers).text
soup = BeautifulSoup(source, 'lxml')
#incrementing total_posts by the number of posts found on the last page, making it accurate
total_posts = int(total_posts) + soup.prettify().count("class=\"thumb\"")
#make sure it doesn't overshoot
if total_posts < repeats or repeats == -1:
    print("Setting amount to max.")
    repeats = total_posts
#convert it to a list to make randomly selecting easier
total_posts = list(range(1, total_posts+1))

tags = tags.replace("+", " ")
inital_repeats_string_len = len(str(repeats))
completed_downloads = 0
i = 0
previous_percentage = ""
while completed_downloads < repeats:
    percentage = f"{(float(completed_downloads) / repeats * 100):.2f}%".rjust(7).ljust(10)
    if percentage != previous_percentage:
        previous_percentage = percentage
        progress_string = f"Progress: {percentage}({str(completed_downloads).rjust(inital_repeats_string_len)} / {str(repeats).rjust(inital_repeats_string_len)})"
        print(progress_string, end="\r")
    time.sleep(0.1)
    if i < repeats:
        threading.Thread(target=download_post).start()
        i += 1

percentage = "100.00%   "
progress_string = f"Progress: {percentage}({str(completed_downloads).rjust(inital_repeats_string_len)} / {str(repeats).rjust(inital_repeats_string_len)})"
print(progress_string)
