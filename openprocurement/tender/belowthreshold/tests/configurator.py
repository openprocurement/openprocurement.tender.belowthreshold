import unittest
from openprocurement.tender.belowthreshold.adapters import TenderBelowThersholdConfigurator


class ConfiguratorValueTest(unittest.TestCase):

    def test_configurator_value(self):
        if hasattr(TenderBelowThersholdConfigurator, 'reverse_awarding_criteria'):
            self.assertEqual(TenderBelowThersholdConfigurator.reverse_awarding_criteria, False)


def suite():
    current_suite = unittest.TestSuite()
    current_suite.addTest(unittest.makeSuite(ConfiguratorValueTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
