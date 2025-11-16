from django.test import TestCase

# Create your tests here.   
class GestionDeStockTest(TestCase):

    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
        self.assertNotEqual(1 + 1, 3)