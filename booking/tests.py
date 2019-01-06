from django.test import TestCase
from booking.models import Participant, DiscountCode
from booking.views import determine_price

# Create your tests here.
class PriceTestCase(TestCase):
    def setUp(self):
        self.prices = {
            'phux': 10,
            'student': 15,
            'other': 25
        }
        # 0 uses, 0 times_used
        unusable_coupon = DiscountCode.objects.create(code='code0', price=1, uses=0)
        # 1 use, 0 times_used
        normal_coupon = DiscountCode.objects.create(code='code1', price=1)
        # 1 use, 1 times_used
        used_coupon = DiscountCode.objects.create(code='code2', price=1, times_used=1)
        # 2 uses, 0 times_used
        mul_nonused_coupon = DiscountCode.objects.create(code='code3', price=1, uses=2)
        # 2 uses, 1 times_used
        mul_halfused_coupon = DiscountCode.objects.create(code='code4', price=1, uses=2, times_used=1)
        # 2 uses, 2 times_used
        mul_used_coupon = DiscountCode.objects.create(code='code5', price=1, uses=2, times_used=2)

    def test_couponprices(self):
        unusable_price = determine_price(True, False, 'other', False, 'code0')
        normal_price = determine_price(True, False, 'other', False, 'code1')
        used_price = determine_price(True, False, 'other', False, 'code2')
        mul_nonused_price = determine_price(True, False, 'other', False, 'code3')
        mul_halfused_price = determine_price(True, False, 'other', False, 'code4')
        mul_used_price = determine_price(True, False, 'other', False, 'code5')
        nonexistant_coupon_price = determine_price(True, False, 'other', False, '')

        self.assertEqual(unusable_price, self.prices['other'])
        self.assertEqual(normal_price, 1)
        self.assertEqual(used_price, self.prices['other'])
        self.assertEqual(mul_nonused_price, 1)
        self.assertEqual(mul_halfused_price, 1)
        self.assertEqual(mul_used_price, self.prices['other'])
        self.assertEqual(nonexistant_coupon_price, self.prices['other'])
