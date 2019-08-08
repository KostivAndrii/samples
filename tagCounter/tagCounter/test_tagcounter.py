import unittest
import tagcounter

class TestStringMethods(unittest.TestCase):

    def test_process_tag_calculating(self):
        self.assertEqual(tagcounter.process_tag_calculating(['title', 'title', 'meta', 'meta', 'meta']), {'title':2, 'meta':3})

    def test_print_dict( self ):
        self.assertEqual(tagcounter.print_dict({'title': 2, 'meta' : 4 , 'div' : 6 }, 'www.google.com'), 'TAG counting for URL:\nwww.google.com\n\ntitle\t\t\t\t\t2  \nmeta\t\t\t\t\t4  \ndiv\t\t\t\t\t6  \n\nРазом:\t\t\t\t\t12')


if __name__ == '__main__':
    unittest.main()