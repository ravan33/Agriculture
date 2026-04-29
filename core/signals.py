"""
Django signals for the gamification and badge system.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Query, Rating, User


@receiver(post_save, sender=Query)
def award_first_query_badge(sender, instance, created, **kwargs):
    """
    Award 'Curious Farmer' badge for first query submission.
    """
    if created and instance.farmer.user_type == 'farmer':
        user = instance.farmer
        # Check if this is the user's first query
        if user.queries.count() == 1:
            if 'curious_farmer' not in user.badges:
                user.badges.append('curious_farmer')
                user.save()


@receiver(post_save, sender=Rating)
def award_rating_badges(sender, instance, created, **kwargs):
    """
    Award badges based on rating behavior.
    """
    if created:
        user = instance.farmer
        
        # Award 'Top Rater' badge for giving a 5-star rating
        if instance.score == 5 and 'top_rater' not in user.badges:
            user.badges.append('top_rater')
            user.save()
        
        # Award 'Feedback Master' badge for giving 10 ratings
        if user.given_ratings.count() >= 10 and 'feedback_master' not in user.badges:
            user.badges.append('feedback_master')
            user.save()


@receiver(post_save, sender=User)
def award_welcome_badge(sender, instance, created, **kwargs):
    """
    Award welcome badge for new users.
    """
    if created:
        if 'welcome' not in instance.badges:
            instance.badges.append('welcome')
            instance.save()


def get_badge_info():
    """
    Return information about all available badges.
    """
    return {
        'welcome': {
            'name': 'Welcome to AgriVision AI',
            'description': 'Awarded for joining the platform',
            'icon': '🎉',
            'color': 'blue'
        },
        'curious_farmer': {
            'name': 'Curious Farmer',
            'description': 'Asked your first question',
            'icon': '🤔',
            'color': 'green'
        },
        'top_rater': {
            'name': 'Top Rater',
            'description': 'Gave a 5-star rating to expert advice',
            'icon': '⭐',
            'color': 'yellow'
        },
        'feedback_master': {
            'name': 'Feedback Master',
            'description': 'Provided feedback on 10+ expert responses',
            'icon': '💬',
            'color': 'purple'
        },
        'active_farmer': {
            'name': 'Active Farmer',
            'description': 'Asked 5+ questions',
            'icon': '🌱',
            'color': 'green'
        },
        'helpful_expert': {
            'name': 'Helpful Expert',
            'description': 'Answered 10+ farmer questions',
            'icon': '🎓',
            'color': 'blue'
        },
        'expert_guru': {
            'name': 'Expert Guru',
            'description': 'Maintained 4.5+ star average rating',
            'icon': '🏆',
            'color': 'gold'
        }
    }
