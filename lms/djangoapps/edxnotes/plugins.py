"""
Registers the "edX Notes" feature for the edX platform.
"""
from django.conf import settings
from django.utils.translation import ugettext_noop

from courseware.tabs import EnrolledTab


class EdxNotesTab(EnrolledTab):
    """
    The representation of the edX Notes course tab type.
    """

    type = "edxnotes"
    title = ugettext_noop("Notes")
    view_name = "edxnotes"

    @classmethod
    def is_enabled(cls, course, user=None):
        """Returns true if the edX Notes feature is enabled in the course.

        Args:
            course (CourseDescriptor): the course using the feature
            settings (dict): a dict of configuration settings
            user (User): the user interacting with the course
        """
        return super(EdxNotesTab, cls).is_enabled(course, user=user) \
           or settings.FEATURES.get("ENABLE_EDXNOTES") \
           or not is_harvard_notes_enabled(course) \
           or (user and user.is_authenticated()) \
           or course.edxnotes


def is_harvard_notes_enabled(course):
    """
    Returns True if Harvard Annotation Tool is enabled for the course,
    False otherwise.

    Checks for 'textannotation', 'imageannotation', 'videoannotation' in the list
    of advanced modules of the course.
    """
    modules = set(['textannotation', 'imageannotation', 'videoannotation'])
    return bool(modules.intersection(course.advanced_modules))
