from django.test import TestCase
from booking.models import Participant, DiscountCode
from booking.views import determine_price

# Create your tests here.
class PriceTestCase(TestCase):
    def setUp(self):
        self.prices = {
            'phux': 10,
            'student': 15,
            'not_student': 25
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

        unusable_price, cheaper_used = determine_price(True, False, 'not_student', False, c0)
        normal_price, cheaper_used = determine_price(True, False, 'not_student', False, c1)
        used_price, cheaper_used = determine_price(True, False, 'not_student', False, c2)
        mul_nonused_price, cheaper_used = determine_price(True, False, 'not_student', False, c3)
        mul_halfused_price, cheaper_used = determine_price(True, False, 'not_student', False, c4)
        mul_used_price, cheaper_used = determine_price(True, False, 'not_student', False, c5)

        self.assertEqual(unusable_price, self.prices['not_student'])
        self.assertEqual(normal_price, 1)
        self.assertEqual(used_price, self.prices['not_student'])
        self.assertEqual(mul_nonused_price, 1)
        self.assertEqual(mul_halfused_price, 1)
        self.assertEqual(mul_used_price, self.prices['not_student'])
