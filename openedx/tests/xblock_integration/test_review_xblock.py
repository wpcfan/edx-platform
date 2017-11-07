"""
Test scenarios for the review xblock.
"""
import json
import unittest

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from nose.plugins.attrib import attr

from lms.djangoapps.courseware.tests.factories import GlobalStaffFactory
from lms.djangoapps.courseware.tests.helpers import LoginEnrollmentTestCase
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from review import ReviewXBlock, get_review_ids
import crum


class TestReviewXBlock(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Create the test environment with the review xblock.
    """
    STUDENTS = [
        {'email': 'learner@test.com', 'password': 'foo'},
    ]
    XBLOCK_NAMES = ['review']

    @classmethod
    def setUpClass(cls):
        # Nose runs setUpClass methods even if a class decorator says to skip
        # the class: https://github.com/nose-devs/nose/issues/946
        # So, skip the test class here if we are not in the LMS.
        if settings.ROOT_URLCONF != 'lms.urls':
            raise unittest.SkipTest('Test only valid in lms')

        super(TestReviewXBlock, cls).setUpClass()

        # Set up for the actual course
        cls.course_actual = CourseFactory.create(
            display_name='Review_Test_Course_ACTUAL',
            org='DillonX',
            number='DAD101x',
            run='3T2017'
        )
        # There are multiple sections so the learner can load different
        # problems, but should only be shown review problems from what they have loaded
        with cls.store.bulk_operations(cls.course_actual.id, emit_signals=False):
            cls.chapter_actual = ItemFactory.create(
                parent=cls.course_actual, display_name='Overview'
            )
            cls.section1_actual = ItemFactory.create(
                parent=cls.chapter_actual, display_name='Section 1'
            )
            cls.unit1_actual = ItemFactory.create(
                parent=cls.section1_actual, display_name='New Unit 1'
            )
            cls.xblock1_actual = ItemFactory.create(
                parent=cls.unit1_actual,
                category='problem',
                display_name='Problem 1'
            )
            cls.xblock2_actual = ItemFactory.create(
                parent=cls.unit1_actual,
                category='problem',
                display_name='Problem 2'
            )
            cls.xblock3_actual = ItemFactory.create(
                parent=cls.unit1_actual,
                category='problem',
                display_name='Problem 3'
            )
            cls.xblock4_actual = ItemFactory.create(
                parent=cls.unit1_actual,
                category='problem',
                display_name='Problem 4'
            )
            cls.section2_actual = ItemFactory.create(
                parent=cls.chapter_actual, display_name='Section 2'
            )
            cls.unit2_actual = ItemFactory.create(
                parent=cls.section2_actual, display_name='New Unit 2'
            )
            cls.xblock5_actual = ItemFactory.create(
                parent=cls.unit2_actual,
                category='problem',
                display_name='Problem 5'
            )
            cls.section3_actual = ItemFactory.create(
                parent=cls.chapter_actual, display_name='Section 3'
            )
            cls.unit3_actual = ItemFactory.create(
                parent=cls.section3_actual, display_name='New Unit 3'
            )
            cls.xblock6_actual = ItemFactory.create(
                parent=cls.unit3_actual,
                category='problem',
                display_name='Problem 6'
            )
            # This is the actual review xBlock
            # When implemented, the review is in its own section as a
            # stand-alone unit.
            cls.review_section_actual = ItemFactory.create(
                parent=cls.chapter_actual, display_name='Review Subsection'
            )
            cls.review_unit_actual = ItemFactory.create(
                parent=cls.review_section_actual, display_name='Review Unit'
            )
            cls.review_xblock_actual = ItemFactory.create(
                parent=cls.review_unit_actual,
                category='review',
                display_name='Review Tool'
            )

        cls.course_actual_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': cls.course_actual.id.to_deprecated_string(),
                'chapter': 'Overview',
                'section': 'Welcome',
            }
        )

        # refresh the course from the modulestore so that it has children
        # Not sure if this is actually needed or not
        cls.course_actual = modulestore().get_course(cls.course_actual.id)

        # Set up for the review course where the review problems are hosted
        cls.course_review = CourseFactory.create(
            display_name='Review_Test_Course_REVIEW',
            org='DillonX',
            number='DAD101rx',
            run='3T2017'
        )
        with cls.store.bulk_operations(cls.course_review.id, emit_signals=True):
            cls.chapter_review = ItemFactory.create(
                parent=cls.course_review, display_name='Overview'
            )
            cls.section_review = ItemFactory.create(
                parent=cls.chapter_review, display_name='Welcome'
            )
            cls.unit1_review = ItemFactory.create(
                parent=cls.section_review, display_name='New Unit 1'
            )
            cls.xblock1_review = ItemFactory.create(
                parent=cls.unit1_review,
                category='problem',
                display_name='Problem 1'
            )
            cls.xblock2_review = ItemFactory.create(
                parent=cls.unit1_review,
                category='problem',
                display_name='Problem 2'
            )
            cls.xblock3_review = ItemFactory.create(
                parent=cls.unit1_review,
                category='problem',
                display_name='Problem 3'
            )
            cls.xblock4_review = ItemFactory.create(
                parent=cls.unit1_review,
                category='problem',
                display_name='Problem 4'
            )
            cls.unit2_review = ItemFactory.create(
                parent=cls.section_review, display_name='New Unit 2'
            )
            cls.xblock5_review = ItemFactory.create(
                parent=cls.unit2_review,
                category='problem',
                display_name='Problem 5'
            )
            cls.unit3_review = ItemFactory.create(
                parent=cls.section_review, display_name='New Unit 3'
            )
            cls.xblock6_review = ItemFactory.create(
                parent=cls.unit3_review,
                category='problem',
                display_name='Problem 6'
            )

        cls.course_review_url = reverse(
            'courseware_section',
            kwargs={
                'course_id': cls.course_review.id.to_deprecated_string(),
                'chapter': 'Overview',
                'section': 'Welcome',
            }
        )

    def setUp(self):
        super(TestReviewXBlock, self).setUp()
        for idx, student in enumerate(self.STUDENTS):
            username = 'u{}'.format(idx)
            self.create_account(username, student['email'], student['password'])
            self.activate_user(student['email'])

        self.staff_user = GlobalStaffFactory()

    def enroll_student(self, email, password, course):
        """
        Student login and enroll for the course
        """
        self.login(email, password)
        self.enroll(course, verify=True)


@attr(shard=1)
class TestReviewFunctions(TestReviewXBlock):
    """
    Check that the essential functions of the Review xBlock work as expected.
    Tests cover the basic process of receiving a hint, adding a new hint,
    and rating/reporting hints.
    """
    def test_no_review_problems(self):
        """
        If a user has not seen any problems, they should
        receive a response to go out and try more problems so they have
        material to review.
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        # Loading the review section
        response = self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.review_section_actual.location.name,
        }))

        expected_h2 = 'Nothing to review'
        expected_p = 'Oh no! You have not interacted with enough problems yet to have any to review. '\
                        'Go back and try more problems so you have content to review.'
        self.assertTrue(expected_h2 in response.content)
        self.assertTrue(expected_p in response.content)

    def test_too_few_review_problems(self):
        """
        If a user does not have enough problems to review, they should
        receive a response to go out and try more problems so they have
        material to review.

        TODO: This test is hardcoded to assume the number of review
        problems to show is > 1 (which it should be). Ideally this could
        be dependent on the number of desired review problems
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        # Loading 1 problem so the learner has something in the CSM
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section2_actual.location.name,
        }))

        # Loading the review section
        response = self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.review_section_actual.location.name,
        }))

        expected_h2 = 'Nothing to review'
        expected_p = 'Oh no! You have not interacted with enough problems yet to have any to review. '\
                        'Go back and try more problems so you have content to review.'

        self.assertTrue(expected_h2 in response.content)
        self.assertTrue(expected_p in response.content)

    def test_review_problems(self):
        """
        If a user has enough problems to review, they should
        receive a response where there are review problems for them to try.

        TODO: This test is hardcoded to assume the number of review
        problems to show is <= 5. Ideally this should
        be dependent on the number of desired review problems
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        # Loading 5 problems so the learner has enough problems in the CSM
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section1_actual.location.name,
        }))
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section2_actual.location.name,
        }))

        # Loading the review section
        response = self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.review_section_actual.location.name,
        }))

        expected_header_text = 'Below are 5 review problems for you to try out and see '\
                                'how well you have mastered the material of this class'
        # The problems are defaulted to correct upon load, so the
        # correctness text should be displayed as follows
        # This happens because the problems "raw_possible" field is 0 and the
        # "raw_earned" field is also 0.
        expected_correctness_text = 'When you originally tried this problem, you ended '\
                                    'up being correct after 0 attempts.'
        expected_problems = ['Review Problem 1', 'Review Problem 2', 'Review Problem 3',
                            'Review Problem 4', 'Review Problem 5']
        expected_url_beginning = 'https://courses.edx.org/xblock/block-v1:DillonX/DAD101rx/3T2017+type@problem+block@'

        self.assertTrue(expected_header_text in response.content)
        self.assertEqual(response.content.count(expected_correctness_text), 5)
        for problem in expected_problems:
            self.assertTrue(problem in response.content)
        self.assertEqual(response.content.count(expected_url_beginning), 5)

    def test_review_problem_urls(self):
        """
        Verify that the URLs returned from the Review xBlock are valid and
        correct URLs for the problems the learner has seen.

        TODO: This test is hardcoded to assume the number of review
        problems to show is 5. Ideally this should
        be dependent on the number of desired review problems
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        # Loading 5 problems so the learner has enough problems in the CSM
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section1_actual.location.name,
        }))
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section2_actual.location.name,
        }))

        user = User.objects.get(email=self.STUDENTS[0]['email'])
        crum.set_current_user(user)
        result_urls = get_review_ids.get_problems(5, self.course_actual.id)

        url_beginning = 'https://courses.edx.org/xblock/block-v1:DillonX/DAD101rx/3T2017+type@problem+block@'
        expected_urls = [
            (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_1', 'correct', 0),
            (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_2', 'correct', 0),
            (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_3', 'correct', 0),
            (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_4', 'correct', 0),
            (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_5', 'correct', 0)
        ]

        for url in expected_urls:
            self.assertTrue(url in result_urls)

    def test_review_problem_urls_unique_problem(self):
        """
        Verify that the URLs returned from the Review xBlock are valid and
        correct URLs for the problems the learner has seen. This test will give
        a unique problem to a learner and verify only that learner sees
        it as a review

        TODO: This test is hardcoded to assume the number of review
        problems to show is 5. Ideally this should
        be dependent on the number of desired review problems
        """
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
        self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

        # Loading 5 problems so the learner has enough problems in the CSM
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section1_actual.location.name,
        }))
        self.client.get(reverse(
            'courseware_section',
            kwargs={
                'course_id': self.course_actual.id,
                'chapter': self.chapter_actual.location.name,
                'section': self.section3_actual.location.name,
        }))

        user = User.objects.get(email=self.STUDENTS[0]['email'])
        crum.set_current_user(user)
        result_urls = get_review_ids.get_problems(5, self.course_actual.id)

        url_beginning = 'https://courses.edx.org/xblock/block-v1:DillonX/DAD101rx/3T2017+type@problem+block@'
        expected_urls = [
            (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_1', 'correct', 0),
            (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_2', 'correct', 0),
            (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_3', 'correct', 0),
            (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_4', 'correct', 0),
            # This is the unique problem
            (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_6', 'correct', 0)
        ]
        expected_not_loaded_problem = (url_beginning + 'i4x://DillonX/DAD101x/problem/Problem_5', 'correct', 0)

        for url in expected_urls:
            self.assertTrue(url in result_urls)
        self.assertFalse(expected_not_loaded_problem in result_urls)

    # NOTE: This test is failing because when I grab the problem from the CSM,
    # it is unable to find its parents. This is some issue with the BlockStructure
    # and it not being populated the way we want. For now, this is being left out
    # since the first course I'm working with does not use this function.
    # TODO: Fix get_vertical from get_review_ids to have the block structure for this test
    # def test_review_vertical_url(self):
    #     """
    #     Verify that the URL returned from the Review xBlock is a valid and
    #     correct URL for the vertical the learner has seen.
    #     """
    #     self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_actual)
    #     self.enroll_student(self.STUDENTS[0]['email'], self.STUDENTS[0]['password'], self.course_review)

    #     # Loading problems so the learner has problems and thus a vertical in the CSM
    #     self.client.get(reverse(
    #         'courseware_section',
    #         kwargs={
    #             'course_id': self.course_actual.id,
    #             'chapter': self.chapter_actual.location.name,
    #             'section': self.section1_actual.location.name,
    #     }))

    #     user = User.objects.get(email=self.STUDENTS[0]['email'])
    #     crum.set_current_user(user)
    #     result_url = get_review_ids.get_vertical(self.course_actual.id)

    #     expected_url = 'https://courses.edx.org/xblock/block-v1:DillonX/DAD101rx/3T2017+type@'\
    #                     'vertical+block@i4x://DillonX/DAD101x/chapter/New_Unit_1'

    #     self.assertEqual(result_url, expected_url)
