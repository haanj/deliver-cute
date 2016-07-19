"""
Cuteness Delivery System.

This program requests the top links from various subreddits of cute animals
and email them to participants.
"""

import os
import re
import sys
import html
import praw
import smtplib
import calendar
import requests
from pytz import timezone
from bs4 import BeautifulSoup
from operator import attrgetter
from itertools import chain, tee
from datetime import date, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "delivercute.settings")
django.setup()
from subscribers.models import Subscriber

try:
    USERNAME = os.environ['USERNAME']
    PASSWORD = os.environ['PASSWORD']
except KeyError:
    print('Global security variables not set.')
    sys.exit()

USER_AGENT = 'python:deliver_cute:v1.0 (by /u/____OOOO____)'
CUTE_SUBS = [
    'AnimalsBeingBros',
    'AnimalsBeingConfused',
    'AnimalsBeingDerps',
    'aww',
    'awwgifs',
    'babybigcatgifs',
    'babyelephantgifs',
    'Eyebleach',
    'gifsofotters',
    'kittengifs',
    'StartledCats',
]
LIMIT = 10

EMAIL_SUBJECT_TEMPLATE = 'Cute Pics for {}'
FROM_NAME = 'Deliver Cute'
PIC_WIDTH = 400
PIC_TEMPLATE = '''
<p>
  <p>
    <a href={permalink}>{title}</a>
    from <a href={subreddit_url}>{subreddit_name}</a>
  </p>
  <p>
    <img src="{url}" style="width:{width}px" alt={title}>
  </p>
</p>
'''

YT_PAT = re.compile(r'.*(youtu\.be|youtube\.com).*')
SRC_PAT = re.compile(r'http(s)?://i\.(imgur|reddituploads|redd).*\.[a-z]{3,4}')


def gather_posts(subreddit_names, limit):
    """Generate image urls from top links in cute subs, sorted by score."""
    reddit = praw.Reddit(user_agent=USER_AGENT)
    subreddits = (reddit.get_subreddit(name) for name in subreddit_names)
    posts = chain(*(sub.get_top_from_day(limit=limit) for sub in subreddits))
    for post in posts:
        print('sub: {} url: {}; score: {}'
              ''.format(post.subreddit, post.url, post.score))
        yield post


def dedupe_posts(posts):
    """Remove duplicate posts."""
    found_already = set()
    for post in posts:
        if post.url not in found_already:
            yield post
            found_already.add(post.url)
        else:
            print('Omitting duplicate {}'.format(post.url))


def fix_image_links(posts):
    """Make sure that each imgur link is directly to the content."""
    for post in posts:
        link = post.url
        if YT_PAT.match(link):
            print('discarding {} as youtube link'.format(link))
            continue

        # Temporary measure until able to display gifv and gyfcat properly
        if link.endswith('gifv') or 'gfycat' in link:
            continue

        if not SRC_PAT.match(link):
            try:
                link = find_source_link(link)
            except AttributeError as e:
                print('Error trying to get img src at {}: {}'.format(link, e))
                continue
        link = re.sub(r'^//', 'http://', link)
        post.url = link
        yield post


def find_source_link(link):
    """Scrape the direct source link from imgur or other website."""
    # Currently only works for imgur
    response = requests.get(link)
    html = BeautifulSoup(response.text, 'html.parser')
    div = html.find('div', class_='post-image')
    img = div.find('img')
    return img.attrs['src']


def get_email_subject():
    """Format today's date into the email subject."""
    today = date.today()
    day_name = calendar.day_name[today.weekday()]
    month_name = calendar.month_name[today.month]
    today_date_str = '{d}, {m} {i} {y}'.format(
        d=day_name,
        m=month_name,
        i=today.day,
        y=today.year,
    )
    return EMAIL_SUBJECT_TEMPLATE.format(today_date_str)


def get_email_body(posts):
    """Format posts into HTML."""
    posts = htmlize_posts(posts)
    return '<html>{}</html>'.format('<br>'.join(posts))


def htmlize_posts(posts):
    """Generate each link as an html-ized image element."""
    for post in posts:
        subreddit = post.subreddit.display_name
        yield PIC_TEMPLATE.format(
            permalink=html.escape(post.permalink),
            url=html.escape(post.url),
            title=html.escape(post.title),
            subreddit_name=html.escape('/r/' + subreddit),
            subreddit_url=html.escape('https://www.reddit.com/r/' + subreddit),
            width=PIC_WIDTH,
        )


def subscribers_for_now():
    """Collect subscribers with send_hour set to current time."""
    now = datetime.now(tz=timezone('US/Pacific'))
    return Subscriber.objects.filter(send_hour=now.hour)


def setup_email_server(username, password):
    """Send an email using gmail's smtp server."""
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(USERNAME, PASSWORD)
    return server


def send_email_from_gmail(server, from_addr, from_name, to_addr, subject, body):
    """Send an email with given server and message info."""
    html = MIMEText(body, 'html')
    msg = MIMEMultipart('alternative')
    msg.attach(html)
    msg['Subject'] = subject
    msg['From'] = from_name
    msg['To'] = to_addr
    server.sendmail(from_addr, to_addr, msg.as_string())


def get_relevant_posts(posts, subscriber):
    """Filter only those posts selected by the current subscriber."""
    for post in posts:
        if post.subreddit.display_name in map(str, subscriber.subreddits.all()):
            yield post


def main(to_addr):
    """Gather then email top cute links."""
    subscribers = subscribers_for_now()
    if not subscribers:
        now = datetime.now(tz=timezone('US/Pacific'))
        print('No subscribers want cute delivered at {}'.format(now.hour))
        return

    subreddits = set(chain(*(s.subreddits.all() for s in subscribers)))
    subreddit_names = map(str, subreddits)
    posts = gather_posts(subreddit_names, LIMIT)
    posts = dedupe_posts(posts)
    posts = fix_image_links(posts)

    subject = get_email_subject()
    server = setup_email_server(USERNAME, PASSWORD)

    for subscriber, posts in zip(subscribers, tee(posts, subscribers.count())):
        relevant_posts = get_relevant_posts(posts, subscriber)
        relevant_posts = sorted(relevant_posts, key=attrgetter('score'), reverse=True)
        body = get_email_body(relevant_posts)
        send_email_from_gmail(server, USERNAME, FROM_NAME, subscriber.email, subject, body)


if __name__ == '__main__':
    try:
        to_addr = sys.argv[1]
    except IndexError:
        to_addr = USERNAME
    main(to_addr)
