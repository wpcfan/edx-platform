import unittest

from django.conf import settings
from django.test import RequestFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from entitlements.api.v1.serializers import CourseEntitlementSerializer
from entitlements.tests.factories import CourseEntitlementFactory


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EntitlementsSerializerTests(ModuleStoreTestCase):
    def setUp(self):
        super(EntitlementsSerializerTests, self).setUp()

    def test_data(self):
        entitlement = CourseEntitlementFactory()
        request = RequestFactory().get('')
        serializer = CourseEntitlementSerializer(entitlement, context={'request': request})

        expected = {
            'user': entitlement.user.username,
            'uuid': str(entitlement.uuid),
            'expired_at': entitlement.expired_at,
            'course_uuid': str(entitlement.course_uuid),
            'mode': entitlement.mode,
            'order_number': entitlement.order_number,
            'created': entitlement.created.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
            'modified': entitlement.modified.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }

        assert serializer.data == expected
