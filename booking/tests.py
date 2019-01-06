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
        c0 = DiscountCode.objects.get(code='code0')
        c1 = DiscountCode.objects.get(code='code1')
        c2 = DiscountCode.objects.get(code='code2')
        c3 = DiscountCode.objects.get(code='code3')
        c4 = DiscountCode.objects.get(code='code4')
        c5 = DiscountCode.objects.get(code='code5')

        unusable_price = determine_price(True, False, 'other', False, c0)
        normal_price = determine_price(True, False, 'other', False, c1)
        used_price = determine_price(True, False, 'other', False, c2)
        mul_nonused_price = determine_price(True, False, 'other', False, c3)
        mul_halfused_price = determine_price(True, False, 'other', False, c4)
        mul_used_price = determine_price(True, False, 'other', False, c5)

        self.assertEqual(unusable_price, self.prices['other'])
        self.assertEqual(normal_price, 1)
        self.assertEqual(used_price, self.prices['other'])
        self.assertEqual(mul_nonused_price, 1)
        self.assertEqual(mul_halfused_price, 1)
        self.assertEqual(mul_used_price, self.prices['other'])
