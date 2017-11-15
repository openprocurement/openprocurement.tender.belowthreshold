# -*- coding: utf-8 -*-
import unittest
from copy import deepcopy

from openprocurement.api.tests.base import snitch

from openprocurement.tender.belowthreshold.tests.base import (
    TenderContentWebTest,
    test_bids,
    test_lots,
    test_organization
)
from openprocurement.tender.belowthreshold.tests.contract_blanks import (
    # TenderContractResourceTest
    create_tender_contract_invalid,
    create_tender_contract,
    create_tender_contract_in_complete_status,
    patch_tender_contract,
    get_tender_contract,
    get_tender_contracts,
    # Tender2LotContractResourceTest
    lot2_patch_tender_contract,
    # TenderContractDocumentResourceTest
    not_found,
    create_tender_contract_document,
    put_tender_contract_document,
    patch_tender_contract_document,
    # Tender2LotContractDocumentResourceTest
    lot2_create_tender_contract_document,
    lot2_put_tender_contract_document,
    lot2_patch_tender_contract_document,
    # TenderMergedContracts2LotsResourceTest
    not_found_contract_for_award,
    try_merge_not_real_award,
    try_merge_itself,
    standstill_period,
    activate_contract_with_complaint,
    cancel_award,
    cancel_main_award,
    merge_two_contracts_with_different_suppliers_id,
    merge_two_contracts_with_different_suppliers_scheme,
    set_big_value,
    value_and_merge_contract_in_one_patch,
    # TenderMergedContracts3LotsResourceTest
    merge_three_contracts,
    standstill_period_3lots,
    activate_contract_with_complaint_3lot,
    cancel_award_3lot,
    cancel_main_award_3lot,
    try_merge_pending_award,
    additional_awards_dateSigned,
    # TenderMergedContracts4LotsResourceTest
    merge_four_contracts,
    sign_contract,
    cancel_award_4lot,
    cancel_main_award_4lot,
    cancel_first_main_award,
    merge_by_two_contracts,
    try_merge_main_contract,
    try_merge_contract_two_times,
    activate_contract_with_complaint_4lot,
    additional_awards_dateSigned_4lot,
)


class TenderContractResourceTestMixin(object):
    test_create_tender_contract_invalid = snitch(create_tender_contract_invalid)
    test_get_tender_contract = snitch(get_tender_contract)
    test_get_tender_contracts = snitch(get_tender_contracts)


class TenderContractDocumentResourceTestMixin(object):
    test_not_found = snitch(not_found)
    test_create_tender_contract_document = snitch(create_tender_contract_document)
    test_put_tender_contract_document = snitch(put_tender_contract_document)
    test_patch_tender_contract_document = snitch(patch_tender_contract_document)


class TenderContractResourceTest(TenderContentWebTest, TenderContractResourceTestMixin):
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(TenderContractResourceTest, self).setUp()
        # Create award
        auth = self.app.authorization
        self.app.authorization = ('Basic', ('token', ''))
        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id'], 'value': self.initial_data["value"], 'items': self.initial_data["items"]}})
        self.app.authorization = auth
        award = response.json['data']
        self.award_id = award['id']
        self.award_value = award['value']
        self.award_suppliers = award['suppliers']
        self.award_items = award['items']
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, self.award_id, self.tender_token), {"data": {"status": "active"}})

    test_create_tender_contract = snitch(create_tender_contract)
    test_create_tender_contract_in_complete_status = snitch(create_tender_contract_in_complete_status)
    test_patch_tender_contract = snitch(patch_tender_contract)


class Tender2LotContractResourceTest(TenderContentWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids
    initial_lots = 2 * test_lots

    def setUp(self):
        super(Tender2LotContractResourceTest, self).setUp()
        # Create award

        auth = self.app.authorization
        self.app.authorization = ('Basic', ('token', ''))
        response = self.app.post_json('/tenders/{}/awards'.format(self.tender_id), {'data': {
            'suppliers': [test_organization],
            'status': 'pending',
            'bid_id': self.initial_bids[0]['id'],
            'lotID': self.initial_lots[0]['id']
        }})
        award = response.json['data']
        self.award_id = award['id']
        self.app.authorization = auth
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, self.award_id, self.tender_token), {"data": {"status": "active"}})

    test_lot2_patch_tender_contract = snitch(lot2_patch_tender_contract)


class TenderContractDocumentResourceTest(TenderContentWebTest, TenderContractDocumentResourceTestMixin):
    initial_status = 'active.qualification'
    initial_bids = test_bids

    def setUp(self):
        super(TenderContractDocumentResourceTest, self).setUp()
        # Create award
        auth = self.app.authorization
        self.app.authorization = ('Basic', ('token', ''))

        response = self.app.post_json('/tenders/{}/awards'.format(
            self.tender_id), {'data': {'suppliers': [test_organization], 'status': 'pending', 'bid_id': self.initial_bids[0]['id']}})
        award = response.json['data']
        self.award_id = award['id']

        self.app.authorization = auth
        response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, self.award_id, self.tender_token), {"data": {"status": "active"}})

        # Create contract for award
        auth = self.app.authorization
        self.app.authorization = ('Basic', ('token', ''))

        response = self.app.post_json('/tenders/{}/contracts'.format(self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
        contract = response.json['data']
        self.contract_id = contract['id']
        self.app.authorization = auth


class Tender2LotContractDocumentResourceTest(TenderContentWebTest):
    initial_status = 'active.qualification'
    initial_bids = test_bids
    initial_lots = 2 * test_lots

    def setUp(self):
        super(Tender2LotContractDocumentResourceTest, self).setUp()
        # Create award
        auth = self.app.authorization
        self.app.authorization = ('Basic', ('token', ''))

        response = self.app.post_json('/tenders/{}/awards'.format(self.tender_id), {'data': {
            'suppliers': [test_organization],
            'status': 'pending',
            'bid_id': self.initial_bids[0]['id'],
            'lotID': self.initial_lots[0]['id']
        }})
        award = response.json['data']
        self.award_id = award['id']

        self.app.authorization = auth
        self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(self.tender_id, self.award_id, self.tender_token), {"data": {"status": "active"}})
        # Create contract for award

        self.app.authorization = ('Basic', ('token', ''))
        response = self.app.post_json('/tenders/{}/contracts'.format(self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
        contract = response.json['data']
        self.contract_id = contract['id']
        self.app.authorization = auth

    lot2_create_tender_contract_document = snitch(lot2_create_tender_contract_document)
    lot2_put_tender_contract_document = snitch(lot2_put_tender_contract_document)
    lot2_patch_tender_contract_document = snitch(lot2_patch_tender_contract_document)


def prepare_bids(init_bids):
    """ Make different indetifier id for every bid """
    init_bids = deepcopy(init_bids)
    base_identifier_id = int(init_bids[0]['tenderers'][0]['identifier']['id'])
    for bid in init_bids:
        base_identifier_id += 1
        bid['tenderers'][0]['identifier']['id'] = "{:0=8}".format(base_identifier_id)
    return init_bids


class TenderMergedContracts2LotsResourceTest(TenderContentWebTest):
    initial_status = 'active.qualification'
    initial_bids = prepare_bids(test_bids)
    initial_lots = deepcopy(2 * test_lots)
    initial_auth = ('Basic', ('broker', ''))

    def create_awards(self):
        authorization = self.app.authorization
        self.app.authorization = ('Basic', ('token', ''))  # set admin role
        # create two awards
        awards_response = list()
        for i in range(len(self.initial_lots)):
            awards_response.append(
                self.app.post_json('/tenders/{}/awards'.format(self.tender_id), {'data': {
                    'suppliers': self.initial_bids[0]['tenderers'],
                    'status': 'pending',
                    'bid_id': self.initial_bids[0]['id'],
                    'value': self.initial_bids[0]['lotValues'][i]['value'],
                    'lotID': self.initial_bids[0]['lotValues'][i]['relatedLot']
                }})
            )

        self.app.authorization = authorization
        return awards_response

    def active_awards(self, *args):
        for award_id in args:
            self.app.patch_json(
                '/tenders/{}/awards/{}?acc_token={}'.format(
                    self.tender_id, award_id, self.tender_token),
                {"data": {"status": "active"}})

    test_not_found_contract_for_award = snitch(not_found_contract_for_award)
    test_try_merge_not_real_award = snitch(try_merge_not_real_award)
    test_try_merge_itself = snitch(try_merge_itself)
    test_standstill_period = snitch(standstill_period)
    test_activate_contract_with_complaint = snitch(activate_contract_with_complaint)
    test_cancel_award = snitch(cancel_award)
    test_cancel_main_award = snitch(cancel_main_award)
    test_merge_two_contracts_with_different_suppliers_id = snitch(merge_two_contracts_with_different_suppliers_id)
    test_merge_two_contracts_with_different_suppliers_scheme = snitch(merge_two_contracts_with_different_suppliers_scheme)
    test_set_big_value = snitch(set_big_value)
    test_value_and_merge_contract_in_one_patch = snitch(value_and_merge_contract_in_one_patch)


class TenderMergedContracts3LotsResourceTest(TenderContentWebTest):
    initial_status = 'active.qualification'
    initial_bids = prepare_bids(test_bids)
    initial_lots = deepcopy(3 * test_lots)
    initial_auth = ('Basic', ('broker', ''))

    test_merge_three_contracts = snitch(merge_three_contracts)
    test_standstill_period_3lots = snitch(standstill_period_3lots)
    test_activate_contract_with_complaint_3lot = snitch(activate_contract_with_complaint_3lot)
    test_cancel_award_3lot = snitch(cancel_award_3lot)
    test_cancel_main_award_3lot = snitch(cancel_main_award_3lot)
    test_try_merge_pending_award = snitch(try_merge_pending_award)
    test_additional_awards_dateSigned = snitch(additional_awards_dateSigned)


class TenderMergedContracts4LotsResourceTest(TenderContentWebTest):
    initial_status = 'active.qualification'
    initial_bids = prepare_bids(test_bids)
    initial_lots = deepcopy(4 * test_lots)
    initial_auth = ('Basic', ('broker', ''))

    test_merge_four_contracts = snitch(merge_four_contracts)
    test_sign_contract = snitch(sign_contract)
    test_cancel_award_4lot = snitch(cancel_award_4lot)
    test_cancel_main_award_4lot = snitch(cancel_main_award_4lot)
    test_cancel_first_main_award = snitch(cancel_first_main_award)
    test_merge_by_two_contracts = snitch(merge_by_two_contracts)
    test_try_merge_main_contract = snitch(try_merge_main_contract)
    test_try_merge_contract_two_times = snitch(try_merge_contract_two_times)
    test_activate_contract_with_complaint_4lot = snitch(activate_contract_with_complaint_4lot)
    test_additional_awards_dateSigned_4lot = snitch(additional_awards_dateSigned_4lot)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TenderContractResourceTest))
    suite.addTest(unittest.makeSuite(TenderContractDocumentResourceTest))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
