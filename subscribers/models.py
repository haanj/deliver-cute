"""Subscriber model tracking preferences for each email."""
from django.db import models as md


def get_hour(n):
    """Convert from 24-hour number range to 12-hour AM/PM format."""
    return (n, '{}:00 {}'.format(n % 12 or 12, 'AM' if n < 12 else 'PM'))

HOUR_CHOICES = map(get_hour, range(24))


class Subscriber(md.Model):
    """Subscriber model tracking preferences for each email."""

    email = md.EmailField()
    send_hour = md.IntegerField(choices=HOUR_CHOICES, default=8)
    subreddits = md.ManyToManyField('SubReddit', related_name='subscribers')

    def __str__(self):
        """String representation of subscriber's email."""
        return self.email

    def subreddit_names(self):
        """Generate just the names of related subreddits."""
        for subreddit in self.subreddits.all():
            yield subreddit.display_name


class SubReddit(md.Model):
    """Subreddit chosen by Subscriber through Many-To-Many Relationship."""

    display_name = md.CharField(max_length=21, unique=True)

    def __str__(self):
        """String representation of subreddit's display name."""
        return self.display_name
