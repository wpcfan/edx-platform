"""
Defines asynchronous celery task for sending email notification (through edx-ace)
pertaining to new discussion forum comments.
"""
import logging
from urllib import urlencode
from urlparse import urljoin

from celery import task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from celery_utils.logged_task import LoggedTask
from edx_ace import ace
from edx_ace.message import MessageType
from edx_ace.recipient import Recipient
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.site_configuration.helpers import get_value
from lms.djangoapps.django_comment_client.utils import permalink
import lms.lib.comment_client as cc
from lms.lib.comment_client.utils import merge_dict

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.schedules.template_context import get_base_template_context


log = logging.getLogger(__name__)


DEFAULT_LANGUAGE = 'en'
ROUTING_KEY = getattr(settings, 'ACE_ROUTING_KEY', None)


class ResponseNotification(MessageType):
    def __init__(self, *args, **kwargs):
        super(ResponseNotification, self).__init__(*args, **kwargs)
        self.name = 'response_notification'


@task(base=LoggedTask, routing_key=ROUTING_KEY)
def send_ace_message(context):
    context['course_id'] = CourseKey.from_string(context['course_id'])

    if _should_send_message(context):
        thread_author = User.objects.get(id=context['thread_author_id'])
        message_context = _build_message_context(context)
        message = ResponseNotification().personalize(
            Recipient(thread_author.username, thread_author.email),
            _get_course_language(context['course_id']),
            message_context
        )
        log.info('Sending forum comment email notification with context %s', message_context)
        ace.send(message)


def _should_send_message(context):
    cc_thread_author = cc.User(id=context['thread_author_id'], course_id=context['course_id'])
    return _is_user_subscribed_to_thread(cc_thread_author, context['thread_id'])


def _is_user_subscribed_to_thread(cc_user, thread_id):
    paginated_result = cc_user.subscribed_threads()
    thread_ids = {thread['id'] for thread in paginated_result.collection}

    while paginated_result.page < paginated_result.num_pages:
        next_page = paginated_result.page + 1
        paginated_result = cc_user.subscribed_threads(query_params={'page': next_page})
        thread_ids.update(thread['id'] for thread in paginated_result.collection)

    return thread_id in thread_ids


def _get_course_language(course_id):
    course_overview = CourseOverview.objects.get(id=course_id)
    language = course_overview.language or DEFAULT_LANGUAGE
    return language


def _build_message_context(context):
    message_context = get_base_template_context(Site.objects.get_current())
    message_context.update(context)
    message_context['post_link'] = _get_thread_url(context)
    message_context['ga_tracking_pixel_url'] = _generate_ga_pixel_url(context['course_id'], context['thread_author_id'])
    return message_context


def _get_thread_url(context):
    thread_content = {
        'type': 'thread',
        'course_id': context['course_id'],
        'commentable_id': context['thread_commentable_id'],
        'id': context['thread_id'],
    }
    return urljoin(settings.LMS_ROOT_URL, permalink(thread_content))


def _generate_ga_pixel_url(course_key, user_id):
    # used for analytics
    query_params = {
        'v': '1',
        't': 'event',
        'ec': 'email',
        'ea': 'open',
        'tid': get_value("GOOGLE_ANALYTICS_TRACKING_ID", settings.GOOGLE_ANALYTICS_TRACKING_ID),
        'uid': user_id,
        'utm_source': 'discussion_notification_email',
        'utm_medium': 'email',
        'cm': 'email',
        'cn': 'discussions_notifications_emails',
        'dp': '/email/ace/discussions/responsenotification/{0}/'.format(course_key),
        'dt': 'To Be Filled In',
    }

    returng u"{url}?{params}".format(
        url="https://www.google-analytics.com/collect",
        params=urlencode(query_params)
    )
