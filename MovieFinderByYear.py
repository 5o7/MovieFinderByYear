# import tools

from googleapiclient.discovery import build
from googlesearch import search
from bs4 import BeautifulSoup
import urllib.request
import requests
import json
import praw
import time
import re

# developer keys used to access data and a youtube build

tmdb_key = "x"
api_key = "x"
youtube = build("youtube", "v3", developerKey=api_key)

# Two variables--one to hold user credentials and another to hold an instance of the website

creds = {"client_id": "ameCCd2j9h0QxgP4IGZbTg",
         "client_secret": "vzg0WWUkKUAbv_gdRKNpir65Nr_eOQ",
         "password": "KillDozer2001!",
         "user_agent": "Find movies",
         "username": "5o7bot"}

reddit = praw.Reddit(client_id=creds["client_id"],
         client_secret=creds["client_secret"],
         password=creds["password"],
         user_agent=creds["user_agent"],
         username=creds["username"])

# The remaining block of code runs every 15 minutes

while True:

    # A list called subreddits to hold website communities

    subreddits = []
    subreddits.append("5o7bot")

    # A list called submissions to store new submissions from movie subs

    submissions = []

    # A list called checked to hold submissions that have already been seen

    checked = []

    # Analyze and collect submissions from all the subreddits (r/5o7bot is the only subreddit in the list)

    for subreddit in subreddits:
        for submission in reddit.subreddit(subreddit).__getattribute__("new")(limit=5):

            try:

                # Check if the submission is in the checked list

                if not any(x in submission.title for x in checked):

                    # Add the submission to the checked list

                    checked.append(submission.title)

                    # Exclude submissions with these words in the title

                    catch_words = ["Lounge", "Weekly", "Monthly", "Announcement", "Features"]
                    if not any(x in submission.title for x in catch_words):

                        # Check if self has commented in the submission

                        task_complete = False
                        for comment in submission.comments:
                            if comment.author == "5o7bot":
                                task_complete = True
                                break

                        # If the criteria is met, add the submission to the submissions list

                        if not task_complete:
                            submissions.append(submission)

            except:
                pass

    # The remaining block of code is run on each submission in the submissions list

    for submission in submissions:

        # Hold the submission title in a variable called movie_year

        movie_year = submission.title

        # Use the submission title (a year) to find the American released movies from a website

        source = requests.get("https://www.the-numbers.com/movies/year/" + movie_year).text
        soup = BeautifulSoup(source, 'lxml')

        # Parse the data and put the movies into a list called movies

        movies = soup.find('div', id='page_filling_chart')
        movies = movies.text
        movies = movies.split('\n\n\n')
        movies = movies[5:]

        # For each movie in the movies list...

        for movie in movies:

            # Create a query using the movie title and "imdb"

            if '\n' in movie:
                movie = movie.split('\n')
                movie = movie[1]
                if "&" in movie:
                    movie = movie.replace("&", "and")

                query = movie + " " + movie_year + " imdb"

                # Using the query get the imdb id with google

                search_results = search(query, 5, 'en')
                for search_result in search_results:
                    if "https://www.imdb.com/title/tt" in search_result:
                        imdb_url = str(search_result)
                        if len(imdb_url) == 37:
                            imdb_id = imdb_url.replace("https://www.imdb.com/title/", "")
                            imdb_id = imdb_id.replace("/", "")
                            break

                # Using the imdb id, get the tmdb info from the movie to find the movie's runtime

                try:
                    info1 = "https://api.themoviedb.org/3/movie/" + imdb_id + "?api_key=" + tmdb_key + "&append_to_response=credits"
                    info1 = requests.get(info1).text
                    info1 = BeautifulSoup(info1, 'lxml')
                    info1 = info1.p.text
                    tmdb_info = json.loads(info1)
                    imdb_runtime = str(tmdb_info["runtime"])

                    query = movie + " " + movie_year

                except:
                    pass

                # Use the query (movie title and year) to search YouTube and get the 20 top results

                try:
                    query = query.replace(" ", "+")
                    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + query)
                    vid_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
                    vid_request = youtube.videos().list(part="contentDetails", id=",".join(vid_ids))
                    vid_response = vid_request.execute()

                    # Create three variables to help quantify the YouTube link runtime

                    hours_pattern = re.compile(r"(\d+)H")
                    minutes_pattern = re.compile(r"(\d+)M")
                    seconds_pattern = re.compile(r"(\d+)S")

                    # For the top 10 results from the YouTube search, do the following...

                    for i in range(0, 10):

                        # Get the content details of each search result

                        vid_response["items"][i]["contentDetails"]

                        # Acquire the uration from the content details

                        duration = vid_response["items"][i]["contentDetails"]["duration"]
                        definition = vid_response["items"][i]["contentDetails"]["definition"]

                        # Create a variable called link to hold the link to the search result

                        link = "https://www.youtube.com/watch?v=" + vid_response["items"][i]["id"]

                        # Convert the runtime into minutes and store it in a variable called total_minutes

                        hours = hours_pattern.search(duration)
                        minutes = minutes_pattern.search(duration)
                        seconds = seconds_pattern.search(duration)

                        hours = int(hours.group(1)) if hours else 0
                        minutes = int(minutes.group(1)) if minutes else 0
                        seconds = int(seconds.group(1)) if seconds else 0

                        total_minutes = hours*60 + minutes + int(seconds/60)

                        # Find the title of the YouTube search result

                        yt_link = "https://www.youtube.com/watch?v=" + vid_ids[i]
                        source2 = requests.get(yt_link).text
                        soup = BeautifulSoup(source, 'lxml')
                        source = requests.get(yt_link).text
                        soup2 = BeautifulSoup(source, 'lxml')
                        yt_info = soup2.find("div", class_="watch-main-col")
                        yt_info = str(yt_info)
                        yt_title = yt_info.split("content=")
                        yt_title = yt_title[1]
                        yt_title = yt_title.split("itemprop=")
                        yt_title = yt_title[0]
                        yt_title = yt_title.replace('"', "")

                        # Create limits to check if the search result runtime is within range of the movie's runtime

                        upper_limit = int(imdb_runtime) + 5
                        lower_limit = int(imdb_runtime) - 5
                        if lower_limit <= total_minutes <= upper_limit:

                            # This is a little hack to refrain from adding YouTube's pay to watch movies

                            try:
                                allowed = vid_response["items"][i]["contentDetails"]["regionRestriction"]["allowed"]
                                allowed = ''.join(allowed)
                                if allowed == "CAUS" or allowed == "US":
                                    break

                            except:
                                pass

                            # Create an entry of the YouTube title, the link, and the definition

                            entry = yt_title + "  \n" + link + "  \n" + definition + "  \n"

                            # Print the entry to the console

                            print(entry)

                            # Enter a comment in the submission

                            submission.reply(entry)
                            break

                except:
                    pass

    # Take a nap

    time.sleep(900)