# -*- coding: utf-8 -*-
from datetime import timedelta
from copy import deepcopy
from uuid import uuid4

from openprocurement.api.utils import get_now

from openprocurement.tender.belowthreshold.tests.base import (
    test_organization
)


# TenderContractResourceTest


def create_tender_contract_invalid(self):
    self.app.authorization = ('Basic', ('token', ''))
    response = self.app.post_json('/tenders/some_id/contracts', {
                                  'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'tender_id'}
    ])

    request_path = '/tenders/{}/contracts'.format(self.tender_id)

    response = self.app.post(request_path, 'data', status=415)
    self.assertEqual(response.status, '415 Unsupported Media Type')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description':
            u"Content-Type header should be one of ['application/json']", u'location': u'header', u'name': u'Content-Type'}
    ])

    response = self.app.post(
        request_path, 'data', content_type='application/json', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'No JSON object could be decoded',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(request_path, 'data', status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Data not available',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(
        request_path, {'not_data': {}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Data not available',
            u'location': u'body', u'name': u'data'}
    ])

    response = self.app.post_json(request_path, {'data': {
                                  'invalid_field': 'invalid_value'}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Rogue field', u'location':
            u'body', u'name': u'invalid_field'}
    ])

    response = self.app.post_json(request_path, {'data': {'awardID': 'invalid_value'}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': [u'awardID should be one of awards'], u'location': u'body', u'name': u'awardID'}
    ])


def create_tender_contract(self):
    self.app.authorization = ('Basic', ('token', ''))
    response = self.app.post_json('/tenders/{}/contracts'.format(
        self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id, 'value': self.award_value, 'suppliers': self.award_suppliers}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    contract = response.json['data']
    self.assertIn('id', contract)
    self.assertIn('value', contract)
    self.assertIn('suppliers', contract)
    self.assertIn(contract['id'], response.headers['Location'])

    tender = self.db.get(self.tender_id)
    tender['contracts'][-1]["status"] = "terminated"
    self.db.save(tender)

    self.set_status('unsuccessful')

    response = self.app.post_json('/tenders/{}/contracts'.format(
        self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't add contract in current (unsuccessful) tender status")

    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"status": "active"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (unsuccessful) tender status")


def create_tender_contract_in_complete_status(self):
    self.app.authorization = ('Basic', ('token', ''))
    response = self.app.post_json('/tenders/{}/contracts'.format(
        self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    contract = response.json['data']
    self.assertIn('id', contract)
    self.assertIn(contract['id'], response.headers['Location'])

    tender = self.db.get(self.tender_id)
    tender['contracts'][-1]["status"] = "terminated"
    self.db.save(tender)

    self.set_status('complete')

    response = self.app.post_json('/tenders/{}/contracts'.format(
    self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't add contract in current (complete) tender status")

    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"status": "active"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")


def patch_tender_contract(self):
    self.app.authorization = ('Basic', ('token', ''))
    response = self.app.get('/tenders/{}/contracts'.format( self.tender_id))
    contract = response.json['data'][0]

    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"status": "active"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertIn("Can't sign contract before stand-still period end (", response.json['errors'][0]["description"])

    self.set_status('complete', {'status': 'active.awarded'})

    token = self.initial_bids_tokens.values()[0]
    response = self.app.post_json('/tenders/{}/awards/{}/complaints?acc_token={}'.format(self.tender_id, self.award_id, token), {'data': {
        'title': 'complaint title',
        'description': 'complaint description',
        'author': test_organization,
        'status': 'claim'
    }})
    self.assertEqual(response.status, '201 Created')
    complaint = response.json['data']
    owner_token = response.json['access']['token']

    tender = self.db.get(self.tender_id)
    for i in tender.get('awards', []):
        i['complaintPeriod']['endDate'] = i['complaintPeriod']['startDate']
    self.db.save(tender)

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"contractID": "myselfID", "items": [{"description": "New Description"}], "suppliers": [{"name": "New Name"}]}})

    response = self.app.get('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']))
    self.assertEqual(response.json['data']['contractID'], contract['contractID'])
    self.assertEqual(response.json['data']['items'], contract['items'])
    self.assertEqual(response.json['data']['suppliers'], contract['suppliers'])

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"value": {"currency": "USD"}}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]["description"], "Can\'t update currency for contract value")

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"value": {"valueAddedTaxIncluded": False}}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]["description"], "Can\'t update valueAddedTaxIncluded for contract value")

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"value": {"amount": 501}}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]["description"], "Value amount should be less or equal to awarded amount (500.0)")

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"value": {"amount": 238}}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['value']['amount'], 238)

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"dateSigned": i['complaintPeriod']['endDate']}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'], [{u'description': [u'Contract signature date should be after award complaint period end date ({})'.format(i['complaintPeriod']['endDate'])], u'location': u'body', u'name': u'dateSigned'}])

    one_hour_in_furure = (get_now() + timedelta(hours=1)).isoformat()
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"dateSigned": one_hour_in_furure}}, status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'], [{u'description': [u"Contract signature date can't be in the future"], u'location': u'body', u'name': u'dateSigned'}])

    custom_signature_date = get_now().isoformat()
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"dateSigned": custom_signature_date}})
    self.assertEqual(response.status, '200 OK')

    response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], self.tender_token), {"data": {
        "status": "answered",
        "resolutionType": "resolved",
        "resolution": "resolution text " * 2
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "answered")
    self.assertEqual(response.json['data']["resolutionType"], "resolved")
    self.assertEqual(response.json['data']["resolution"], "resolution text " * 2)

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"status": "active"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't sign contract before reviewing all complaints")

    response = self.app.patch_json('/tenders/{}/awards/{}/complaints/{}?acc_token={}'.format(self.tender_id, self.award_id, complaint['id'], owner_token), {"data": {
        "satisfied": True,
        "status": "resolved"
    }})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "resolved")

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"status": "active"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "active")

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"value": {"amount": 232}}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"contractID": "myselfID"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"items": [{"description": "New Description"}]}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"suppliers": [{"name": "New Name"}]}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"status": "active"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update contract in current (complete) tender status")

    response = self.app.patch_json('/tenders/{}/contracts/some_id?acc_token={}'.format(self.tender_id, self.tender_token), {"data": {"status": "active"}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'contract_id'}
    ])

    response = self.app.patch_json('/tenders/some_id/contracts/some_id?acc_token={}'.format(self.tender_token), {"data": {"status": "active"}}, status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.get('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data']["status"], "active")
    self.assertEqual(response.json['data']["value"]['amount'], 238)
    self.assertEqual(response.json['data']['contractID'], contract['contractID'])
    self.assertEqual(response.json['data']['items'], contract['items'])
    self.assertEqual(response.json['data']['suppliers'], contract['suppliers'])
    self.assertEqual(response.json['data']['dateSigned'], custom_signature_date)


def get_tender_contract(self):
    self.app.authorization = ('Basic', ('token', ''))
    response = self.app.post_json('/tenders/{}/contracts'.format(
        self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    contract = response.json['data']

    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}/contracts/{}'.format(self.tender_id, contract['id']))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'], contract)

    response = self.app.get('/tenders/{}/contracts/some_id'.format(self.tender_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'contract_id'}
    ])

    response = self.app.get('/tenders/some_id/contracts/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])


def get_tender_contracts(self):
    self.app.authorization = ('Basic', ('token', ''))
    response = self.app.post_json('/tenders/{}/contracts'.format(
        self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    contract = response.json['data']

    self.app.authorization = ('Basic', ('broker', ''))
    response = self.app.get('/tenders/{}/contracts'.format(self.tender_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['data'][-1], contract)

    response = self.app.get('/tenders/some_id/contracts', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])


# Tender2LotContractResourceTest


def lot2_patch_tender_contract(self):
    auth = self.app.authorization
    self.app.authorization = ('Basic', ('token', ''))

    response = self.app.post_json('/tenders/{}/contracts'.format(
        self.tender_id), {'data': {'title': 'contract title', 'description': 'contract description', 'awardID': self.award_id}})
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    contract = response.json['data']
    self.app.authorization = auth

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"status": "active"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertIn("Can't sign contract before stand-still period end (", response.json['errors'][0]["description"])

    self.set_status('complete', {'status': 'active.awarded'})

    response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(self.tender_id, self.tender_token), {'data': {
        'reason': 'cancellation reason',
        'status': 'active',
        "cancellationOf": "lot",
        "relatedLot": self.initial_lots[0]['id']
    }})

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, contract['id'], self.tender_token), {"data": {"status": "active"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update contract only in active lot status")


# TenderContractDocumentResourceTest


def not_found(self):
    response = self.app.post('/tenders/some_id/contracts/some_id/documents?acc_token={}'.format(self.tender_token), status=404, upload_files=[
                             ('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.post('/tenders/{}/contracts/some_id/documents?acc_token={}'.format(self.tender_id, self.tender_token), status=404, upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'contract_id'}
    ])

    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(self.tender_id, self.contract_id, self.tender_token), status=404, upload_files=[
                             ('invalid_value', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'body', u'name': u'file'}
    ])

    response = self.app.get('/tenders/some_id/contracts/some_id/documents', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.get('/tenders/{}/contracts/some_id/documents'.format(self.tender_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'contract_id'}
    ])

    response = self.app.get('/tenders/some_id/contracts/some_id/documents/some_id', status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.get('/tenders/{}/contracts/some_id/documents/some_id'.format(self.tender_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'contract_id'}
    ])

    response = self.app.get('/tenders/{}/contracts/{}/documents/some_id'.format(self.tender_id, self.contract_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'document_id'}
    ])

    response = self.app.put('/tenders/some_id/contracts/some_id/documents/some_id?acc_token={}'.format(self.tender_token), status=404,
                            upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'tender_id'}
    ])

    response = self.app.put('/tenders/{}/contracts/some_id/documents/some_id?acc_token={}'.format(self.tender_id, self.tender_token), status=404, upload_files=[
                            ('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'url', u'name': u'contract_id'}
    ])

    response = self.app.put('/tenders/{}/contracts/{}/documents/some_id?acc_token={}'.format(
        self.tender_id, self.contract_id, self.tender_token), status=404, upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'document_id'}
    ])


def create_tender_contract_document(self):
    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
        self.tender_id, self.contract_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual('name.doc', response.json["data"]["title"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/contracts/{}/documents'.format(self.tender_id, self.contract_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual('name.doc', response.json["data"][0]["title"])

    response = self.app.get('/tenders/{}/contracts/{}/documents?all=true'.format(self.tender_id, self.contract_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"][0]["id"])
    self.assertEqual('name.doc', response.json["data"][0]["title"])

    response = self.app.get('/tenders/{}/contracts/{}/documents/{}?download=some_id'.format(
        self.tender_id, self.contract_id, doc_id), status=404)
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location': u'url', u'name': u'download'}
    ])

    response = self.app.get('/tenders/{}/contracts/{}/documents/{}?{}'.format(
        self.tender_id, self.contract_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 7)
    self.assertEqual(response.body, 'content')

    response = self.app.get('/tenders/{}/contracts/{}/documents/{}'.format(
        self.tender_id, self.contract_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('name.doc', response.json["data"]["title"])

    tender = self.db.get(self.tender_id)
    tender['contracts'][-1]["status"] = "cancelled"
    self.db.save(tender)

    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
        self.tender_id, self.contract_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current contract status")

    self.set_status('{}'.format(self.forbidden_contract_document_modification_actions_status))

    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
        self.tender_id, self.contract_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't add document in current ({}) tender status".format(self.forbidden_contract_document_modification_actions_status))


def put_tender_contract_document(self):
    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
        self.tender_id, self.contract_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.put('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(self.tender_id, self.contract_id, doc_id, self.tender_token),
                            status=404,
                            upload_files=[('invalid_name', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'body', u'name': u'file'}
    ])

    response = self.app.put('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.contract_id, doc_id, self.tender_token), upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/contracts/{}/documents/{}?{}'.format(
        self.tender_id, self.contract_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 8)
    self.assertEqual(response.body, 'content2')

    response = self.app.get('/tenders/{}/contracts/{}/documents/{}'.format(
        self.tender_id, self.contract_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('name.doc', response.json["data"]["title"])

    response = self.app.put('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.contract_id, doc_id, self.tender_token), 'content3', content_type='application/msword')
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.get('/tenders/{}/contracts/{}/documents/{}?{}'.format(
        self.tender_id, self.contract_id, doc_id, key))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/msword')
    self.assertEqual(response.content_length, 8)
    self.assertEqual(response.body, 'content3')

    tender = self.db.get(self.tender_id)
    tender['contracts'][-1]["status"] = "cancelled"
    self.db.save(tender)

    response = self.app.put('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.contract_id, doc_id, self.tender_token), upload_files=[('file', 'name.doc', 'content3')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current contract status")

    self.set_status('{}'.format(self.forbidden_contract_document_modification_actions_status))

    response = self.app.put('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.contract_id, doc_id, self.tender_token), upload_files=[('file', 'name.doc', 'content3')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current ({}) tender status".format(self.forbidden_contract_document_modification_actions_status))


def patch_tender_contract_document(self):
    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
        self.tender_id, self.contract_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(self.tender_id, self.contract_id, doc_id, self.tender_token), {"data": {"description": "document description"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])

    response = self.app.get('/tenders/{}/contracts/{}/documents/{}'.format(
        self.tender_id, self.contract_id, doc_id))
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    self.assertEqual('document description', response.json["data"]["description"])

    tender = self.db.get(self.tender_id)
    tender['contracts'][-1]["status"] = "cancelled"
    self.db.save(tender)

    response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(self.tender_id, self.contract_id, doc_id, self.tender_token), {"data": {"description": "document description"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current contract status")

    self.set_status('{}'.format(self.forbidden_contract_document_modification_actions_status))

    response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(self.tender_id, self.contract_id, doc_id, self.tender_token), {"data": {"description": "document description"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can't update document in current ({}) tender status".format(self.forbidden_contract_document_modification_actions_status))


# Tender2LotContractDocumentResourceTest


def lot2_create_tender_contract_document(self):
    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
        self.tender_id, self.contract_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])
    self.assertEqual('name.doc', response.json["data"]["title"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(self.tender_id, self.tender_token), {'data': {
        'reason': 'cancellation reason',
        'status': 'active',
        "cancellationOf": "lot",
        "relatedLot": self.initial_lots[0]['id']
    }})

    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
        self.tender_id, self.contract_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can add document only in active lot status")


def lot2_put_tender_contract_document(self):
    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
        self.tender_id, self.contract_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.put('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(self.tender_id, self.contract_id, doc_id, self.tender_token),
                            status=404,
                            upload_files=[('invalid_name', 'name.doc', 'content')])
    self.assertEqual(response.status, '404 Not Found')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['status'], 'error')
    self.assertEqual(response.json['errors'], [
        {u'description': u'Not Found', u'location':
            u'body', u'name': u'file'}
    ])

    response = self.app.put('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.contract_id, doc_id, self.tender_token), upload_files=[('file', 'name.doc', 'content2')])
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])
    key = response.json["data"]["url"].split('?')[-1]

    response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(self.tender_id, self.tender_token), {'data': {
        'reason': 'cancellation reason',
        'status': 'active',
        "cancellationOf": "lot",
        "relatedLot": self.initial_lots[0]['id']
    }})

    response = self.app.put('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(
        self.tender_id, self.contract_id, doc_id, self.tender_token), upload_files=[('file', 'name.doc', 'content3')], status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")


def lot2_patch_tender_contract_document(self):
    response = self.app.post('/tenders/{}/contracts/{}/documents?acc_token={}'.format(
        self.tender_id, self.contract_id, self.tender_token), upload_files=[('file', 'name.doc', 'content')])
    self.assertEqual(response.status, '201 Created')
    self.assertEqual(response.content_type, 'application/json')
    doc_id = response.json["data"]['id']
    self.assertIn(doc_id, response.headers['Location'])

    response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(self.tender_id, self.contract_id, doc_id, self.tender_token), {"data": {"description": "document description"}})
    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(doc_id, response.json["data"]["id"])

    response = self.app.post_json('/tenders/{}/cancellations?acc_token={}'.format(self.tender_id, self.tender_token), {'data': {
        'reason': 'cancellation reason',
        'status': 'active',
        "cancellationOf": "lot",
        "relatedLot": self.initial_lots[0]['id']
    }})

    response = self.app.patch_json('/tenders/{}/contracts/{}/documents/{}?acc_token={}'.format(self.tender_id, self.contract_id, doc_id, self.tender_token), {"data": {"description": "new document description"}}, status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.content_type, 'application/json')
    self.assertEqual(response.json['errors'][0]["description"], "Can update document only in active lot status")
    
    
# TenderMergedContracts2LotsResourceTest


def not_found_contract_for_award(self):
    """ Try merge contract which doesn't exist """
    first_award, second_award = self.create_awards()
    first_award_id = first_award.json['data']['id']
    second_award_id = second_award.json['data']['id']
    self.active_awards(first_award_id)

    #  Get second award and change status to active
    #  but don't create contract
    tender = self.db.get(self.tender_id)
    second_award = tender['awards'][1]
    second_award['status'] = 'active'
    self.db.save(tender)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    contracts = response.json['data']

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contracts[0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": [second_award_id]}},
        status=422)

    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'],
                     [
                         {
                             "location": "body",
                             "name": "additionalAwardIDs",
                             "description": [
                                 "Can't found contract for award {award_id}".format(award_id=second_award_id)
                             ]
                         }
                     ])


def try_merge_not_real_award(self):
    """ Can't merge award which doesn't exist """
    first_award, second_award = self.create_awards()
    first_award_id = first_award.json['data']['id']
    second_award_id = second_award.json['data']['id']

    self.active_awards(first_award_id, second_award_id)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    # Try send not real award id
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": [uuid4().hex]}},
        status=422)

    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'], [{u'description': [u'id must be one of award id'], u'location': u'body', u'name': u'additionalAwardIDs'}])


def try_merge_itself(self):
    """ Can't merge contract if self contract """

    first_award, second_award = self.create_awards()
    first_award_id = first_award.json['data']['id']
    second_award_id = second_award.json['data']['id']
    self.active_awards(first_award_id, second_award_id)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    # Try send itself
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": [first_contract['awardID']]}},
        status=422)

    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'],
                     [
                         {
                             "location": "body",
                             "name": "additionalAwardIDs",
                             "description": ["Can't merge itself"]
                         }
                     ])


def standstill_period(self):
    """ Create two awards and merged them and try set status active for main
        contract while additional award has stand still period  """
    first_award, second_award = self.create_awards()
    first_award_id = first_award.json['data']['id']
    second_award_id = second_award.json['data']['id']

    self.active_awards(first_award_id, second_award_id)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(
        self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract['id'], second_contract['mergedInto'])
    self.assertEqual(second_contract['status'], 'merged')

    # Update complaintPeriod for additional award
    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][0]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now + timedelta(days=1)).isoformat(),
                                              "endDate": (now + timedelta(days=1)).isoformat()}
    self.db.save(tender)

    dateSigned = get_now().isoformat()
    # Try set status active for main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"status": "active"}},
        status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertIn("Can't sign contract before stand-still additional awards period end",
                  response.json['errors'][0]['description'])

    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][0]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)
    # Try set status active for main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned, "status": "active"}})

    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'active')
    self.assertEqual(response.json['data']['dateSigned'], dateSigned)


def activate_contract_with_complaint(self):
    first_award, second_award = self.create_awards()
    first_award_id = first_award.json['data']['id']
    second_award_id = second_award.json['data']['id']
    self.active_awards(first_award_id, second_award_id)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(
        self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract['id'], second_contract['mergedInto'])
    self.assertEqual(second_contract['status'], 'merged')

    bid1_token = self.db[self.tender_id]['bids'][0]['owner_token']
    # Create complaint on additional award
    response = self.app.post_json('/tenders/{}/awards/{}/complaints?acc_token={}'.format(self.tender_id, second_contract['awardID'], bid1_token),
                                  {'data': {
                                      'title': 'complaint title',
                                      'description': 'complaint description',
                                      'author': test_organization,
                                      'status': 'claim'
                                  }})
    self.assertEqual(response.status, '201 Created')
    complaint = response.json['data']
    owner_token = response.json['access']['token']

    # Update complaintPeriod for additional award
    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][0]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)

    # Lets resolve complaint
    self.edit_award_complaint(second_contract['awardID'], complaint['id'], self.tender_token,
                            {"data": {"status": "answered",
                                      "resolutionType": "resolved",
                                      "resolution": "resolution text " * 2}
                            })

    # Try set status active for main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": get_now().isoformat(), "status": "active"}},
        status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [{u'description': u"Can't sign contract before reviewing all complaints", u'location': u'body', u'name': u'data'}])

    self.edit_award_complaint(second_contract['awardID'], complaint['id'], owner_token,
        {"data": {"satisfied": True, "status": "resolved"}})

    # And try sign contract again
    dateSigned = get_now().isoformat()
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned, "status": "active"}})

    self.assertEqual(response.json['data']['status'], 'active')
    self.assertEqual(response.json['data']['dateSigned'], dateSigned)


def cancel_award(self):
    """ Create two awards and merged them and then cancel additional award """
    first_award, second_award = self.create_awards()
    first_award_id = first_award.json['data']['id']
    second_award_id = second_award.json['data']['id']
    self.active_awards(first_award_id, second_award_id)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(
        self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract['id'], second_contract['mergedInto'])
    self.assertEqual(second_contract['status'], 'merged')

    # Cancel additional award
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
        self.tender_id, second_award_id, self.tender_token),
        {'data': {'status': 'cancelled'}}, status=403)

    self.assertEqual(response.status, "403 Forbidden")
    self.assertEqual(response.json['errors'][0]['description'], "Can't cancel award while it is a part of merged contracts.")


def cancel_main_award(self):
    """ Create two awards and merged them and then cancel main award """
    first_award, second_award = self.create_awards()
    first_award_id = first_award.json['data']['id']
    second_award_id = second_award.json['data']['id']
    self.active_awards(first_award_id, second_award_id)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(
        self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract['id'], second_contract['mergedInto'])
    self.assertEqual(second_contract['status'], 'merged')

    # Cancel additional award
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
        self.tender_id, first_award_id, self.tender_token),
        {'data': {'status': 'cancelled'}})

    self.assertEqual(response.status, "200 OK")

    # Check cancel award
    response = self.app.get('/tenders/{}/contracts/{}?acc_token'.format(
        self.tender_id, first_contract['id'], self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(response.json['data']['status'], 'cancelled')

    # Check contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 2)
    self.assertNotIn('additionalAwardIDs', response.json['data'][0])
    self.assertEqual(response.json['data'][1]['status'], 'pending')

    # Check that new award was created and has status pending
    response = self.app.get('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(response.json['data'][-1]['status'], 'pending')


def merge_two_contracts_with_different_suppliers_id(self):
    """ Try merge contract with different susppliers """

    authorization = self.app.authorization
    self.app.authorization = ('Basic', ('token', ''))  # set admin role
    # create two awards
    first_award_response = self.app.post_json('/tenders/{}/awards'.format(self.tender_id),
                                              {'data': {'suppliers': self.initial_bids[0]['tenderers'],
                                                        'status': 'pending',
                                                        'bid_id': self.initial_bids[0]['id'],
                                                        'value': self.initial_bids[0]['lotValues'][0]['value'],
                                                        'lotID': self.initial_bids[0]['lotValues'][0]['relatedLot']}})

    second_award_response = self.app.post_json('/tenders/{}/awards'.format(self.tender_id),
                                               {'data': {'suppliers': self.initial_bids[1]['tenderers'],
                                                         'status': 'pending',
                                                         'bid_id': self.initial_bids[0]['id'],
                                                         'value': self.initial_bids[1]['lotValues'][1]['value'],
                                                         'lotID': self.initial_bids[1]['lotValues'][1]['relatedLot']}})

    print '===============', self.initial_bids[1]['tenderers']
    print '----------------', self.initial_bids[0]['tenderers']

    first_award = first_award_response.json['data']
    first_award_id = first_award['id']
    second_award = second_award_response.json['data']
    second_award_id = second_award['id']
    self.active_awards(first_award_id, second_award_id)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    # Try merge first contract to second
    additionalAwardIDs = [second_contract['awardID']]
    response = self.app.patch_json(
        '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}},
        status=422)

    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'],
                     [
                         {
                             "location": "body",
                             "name": "additionalAwardIDs",
                             "description": ["Awards must have same suppliers id"]
                         }
                     ])

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(
        self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    self.assertNotIn('additionalAwardIDs', first_contract)
    self.assertNotIn('mergedInto', second_contract)
    self.assertNotEqual(second_contract['status'], 'merged')


def merge_two_contracts_with_different_suppliers_scheme(self):
    """ Try merge contract with different susppliers scheme """

    authorization = self.app.authorization
    self.app.authorization = ('Basic', ('token', ''))  # set admin role
    # set different scheme
    initial_bids = deepcopy(self.initial_bids)
    initial_bids[0]['tenderers'][0]['identifier']['scheme'] = 'UA-EDR'
    initial_bids[1]['tenderers'][0]['identifier']['scheme'] = 'LV-RE'
    initial_bids[1]['tenderers'][0]['identifier']['id'] = initial_bids[0]['tenderers'][0]['identifier']['id']
    # create two awards
    first_award_response = self.app.post_json('/tenders/{}/awards'.format(self.tender_id),
                                              {'data': {'suppliers': initial_bids[0]['tenderers'],
                                                        'status': 'pending',
                                                        'bid_id': initial_bids[0]['id'],
                                                        'value': initial_bids[0]['lotValues'][0]['value'],
                                                        'lotID': initial_bids[0]['lotValues'][0]['relatedLot']}})

    second_award_response = self.app.post_json('/tenders/{}/awards'.format(self.tender_id),
                                               {'data': {'suppliers': initial_bids[1]['tenderers'],
                                                         'status': 'pending',
                                                         'bid_id': initial_bids[0]['id'],
                                                         'value': initial_bids[1]['lotValues'][1]['value'],
                                                         'lotID': initial_bids[1]['lotValues'][1]['relatedLot']}})

    first_award = first_award_response.json['data']
    first_award_id = first_award['id']
    second_award = second_award_response.json['data']
    second_award_id = second_award['id']
    self.active_awards(first_award_id, second_award_id)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID']]
    response = self.app.patch_json(
        '/tenders/{}/contracts/{}?acc_token={}'.format(self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}},
        status=422)

    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'],
                     [
                         {
                             "location": "body",
                             "name": "additionalAwardIDs",
                             "description": ["Awards must have same suppliers schema"]
                         }
                     ])

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(
        self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    self.assertNotIn('additionalAwardIDs', first_contract)
    self.assertNotIn('mergedInto', second_contract)
    self.assertNotEqual(second_contract['status'], 'merged')


def set_big_value(self):
    """ Create two awards and merged them """
    first_award, second_award = self.create_awards()
    first_award_id = first_award.json['data']['id']
    second_award_id = second_award.json['data']['id']
    self.active_awards(first_award_id, second_award_id)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(
        self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract['id'], second_contract['mergedInto'])
    self.assertEqual(second_contract['status'], 'merged')

    max_value = first_contract["value"]["amount"] + second_award.json['data']["value"]["amount"]
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"value": {"amount": max_value + 0.1}}}, status=403)

    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'][0]["description"],
                     "Value amount should be less or equal to awarded amount ({value:.1f})".format(value=max_value))


def value_and_merge_contract_in_one_patch(self):
    """ Set new value and merge contract in one  """
    first_award, second_award = self.create_awards()
    first_award_id = first_award.json['data']['id']
    second_award_id = second_award.json['data']['id']
    self.active_awards(first_award_id, second_award_id)

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID']]

    max_value = first_contract["value"]["amount"] + second_award.json['data']["value"]["amount"]

    self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"value": {"amount": max_value},
                  "additionalAwardIDs": additionalAwardIDs}})

# TenderMergedContracts3LotsResourceTest

def merge_three_contracts(self):
    """ Create two awards and merged them """

    awards = self.create_awards()
    self.active_awards(awards)

    # get created contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract, third_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID'], third_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], third_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(third_contract["status"], "merged")

    # set stand still period
    tender = self.db.get(self.tender_id)
    now = get_now()
    for award in tender['awards']:
        award['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                    "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)

    # Set status active for first contract
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {'data': {'status': 'active'}})

    self.assertEqual(response.json['data']['status'], 'active')
    # and check tender status
    response = self.app.get('/tenders/{}'.format(self.tender_id))
    self.assertEqual(response.json['data']['status'], 'complete')


def standstill_period_3lots(self):
    """ Create two awards and merged them and try set status active for main
        contract while additional award has stand still period  """

    # create and active awards
    awards = self.create_awards()
    self.active_awards(awards)

    # get created contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract, third_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID'], third_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], third_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(third_contract["status"], "merged")

    # Update complaintPeriod for additional award
    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][0]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][2]['complaintPeriod'] = {"startDate": (now + timedelta(days=1)).isoformat(),
                                              "endDate": (now + timedelta(days=1)).isoformat()}
    self.db.save(tender)

    dateSigned = get_now().isoformat()
    # Try set status active for main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"status": "active"}},
        status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertIn("Can't sign contract before stand-still additional awards period end",
                  response.json['errors'][0]['description'])

    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][0]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][2]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)
    # Try set status active for main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned, "status": "active"}})

    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['status'], 'active')
    self.assertEqual(response.json['data']['dateSigned'], dateSigned)


def activate_contract_with_complaint_3lot(self):

    awards = self.create_awards()
    self.active_awards(awards)

    # get created contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract, third_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID'], third_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], third_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(third_contract["status"], "merged")

    # Create complaint on first additional award
    bid1_token = self.db[self.tender_id]['bids'][0]['owner_token']
    response = self.app.post_json('/tenders/{}/awards/{}/complaints?acc_token={}'.format(self.tender_id, second_contract['awardID'], bid1_token),
                                  {'data': {
                                      'title': 'complaint title',
                                      'description': 'complaint description',
                                      'author': test_organization,
                                      'status': 'claim'
                                  }})
    self.assertEqual(response.status, '201 Created')
    second_award_complaint = response.json['data']
    second_award_complaint_owner_token = response.json['access']['token']

    # Create complaint on second additional award
    response = self.app.post_json(
        '/tenders/{}/awards/{}/complaints?acc_token={}'.format(self.tender_id, third_contract['awardID'], bid1_token),
        {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': test_organization,
            'status': 'claim'
        }})
    self.assertEqual(response.status, '201 Created')
    third_award_complaint = response.json['data']
    third_award_complaint_owner_token = response.json['access']['token']

    # Update complaintPeriod for awards
    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][0]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][2]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)

    # Lets resolve first complaint
    self.edit_award_complaint(second_contract['awardID'],
                           second_award_complaint['id'],
                           self.tender_token,
                           {"data": {"status": "answered",
                                          "resolutionType": "resolved",
                                          "resolution": "resolution text " * 2}
                                      })

    # Try set status active for main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": get_now().isoformat(), "status": "active"}},
        status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [{u'description': u"Can't sign contract before reviewing all complaints", u'location': u'body', u'name': u'data'}])

    self.edit_award_complaint(second_contract['awardID'],
                       second_award_complaint['id'],
                       second_award_complaint_owner_token,
                       {"data": {"satisfied": True, "status": "resolved"}})

    # Lets resolve second complaint
    self.edit_award_complaint(third_contract['awardID'],
                           third_award_complaint['id'],
                           self.tender_token,
                           {"data": {"status": "answered", "resolutionType": "resolved",
                                                     "resolution": "resolution text " * 2}})

    # Try set status active for main contract again
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": get_now().isoformat(), "status": "active"}},
        status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [{u'description': u"Can't sign contract before reviewing all complaints", u'location': u'body', u'name': u'data'}])

    self.edit_award_complaint(third_contract['awardID'],
                           third_award_complaint['id'],
                           third_award_complaint_owner_token,
                           {"data": {"satisfied": True, "status": "resolved"}})

    # And try sign contract again
    dateSigned = get_now().isoformat()
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned, "status": "active"}})

    self.assertEqual(response.json['data']['status'], 'active')
    self.assertEqual(response.json['data']['dateSigned'], dateSigned)


def cancel_award_3lot(self):
    """ Create two awards and merged them and try to cancel both """
    awards = self.create_awards()
    self.active_awards(awards)

    # get created contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract, third_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID'], third_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], third_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(third_contract["status"], "merged")

    # Cancel additional award
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
        self.tender_id, second_contract['awardID'], self.tender_token),
        {'data': {'status': 'cancelled'}}, status=403)

    self.assertEqual(response.status, "403 Forbidden")
    self.assertEqual(response.json['errors'][0]['description'], "Can't cancel award while it is a part of merged contracts.")

    # Check main contract
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(len(response.json['data'][0]['additionalAwardIDs']), 2)

    # Cancel second additional award
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
        self.tender_id, third_contract['awardID'], self.tender_token),
        {'data': {'status': 'cancelled'}}, status=403)

    self.assertEqual(response.status, "403 Forbidden")
    self.assertIn("Can\'t cancel award while it is a part of merged contracts.",
            response.json['errors'][0]['description'])

    # Check main contract
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(len(response.json['data'][0]['additionalAwardIDs']), 2)


def cancel_main_award_3lot(self):
    """ Create two awards and merged them and then cancel main contract """
    awards = self.create_awards()
    self.active_awards(awards)

    # get created contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract, third_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID'], third_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], third_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(third_contract["status"], "merged")

    # Cancel additional award
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
        self.tender_id, first_contract['awardID'], self.tender_token),
        {'data': {'status': 'cancelled'}})

    self.assertEqual(response.status, "200 OK")

    # Check cancelled award
    response = self.app.get('/tenders/{}/contracts/{}?acc_token'.format(
        self.tender_id, first_contract['id'], self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(response.json['data']['status'], 'cancelled')
    self.assertNotIn('additionalAwardIDs', response.json['data']['status'])

    # Check rest contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 3)
    self.assertEqual(response.json['data'][1]['status'], 'pending')
    self.assertEqual(response.json['data'][2]['status'], 'pending')

    # Check that new awards were created and has status pending
    response = self.app.get('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 4)
    self.assertEqual(response.json['data'][-1]['status'], 'pending')


def try_merge_pending_award(self):
    awards = self.create_awards()
    self.active_awards(awards[:-1])

    # get created contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract = response.json['data']

    # for third award didn't create contract
    additionalAwardIDs = [second_contract['awardID'], awards[-1].json['data']['id']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}},
        status=422)

    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertEqual(response.json['errors'],
                     [
                         {
                             "location": "body",
                             "name": "additionalAwardIDs",
                             "description": ["awards must has status active"]
                         }
                     ])

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract = response.json['data']
    self.assertNotIn('additionalAwardIDs', first_contract)
    self.assertNotIn('mergedInto', second_contract)
    self.assertNotEqual(second_contract["status"], "merged")


def additional_awards_dateSigned(self):
    """ Try set dateSigned before end complaint period for additional awards """

    awards = self.create_awards()
    self.active_awards(awards)

    # get created contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract, third_contract = response.json['data']

    additionalAwardIDs = [second_contract['awardID'], third_contract['awardID']]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], third_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(third_contract["status"], "merged")

    # Update complaintPeriod for additional award
    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][0]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][2]['complaintPeriod'] = {"startDate": (now + timedelta(days=1)).isoformat(),
                                              "endDate": (now + timedelta(days=1)).isoformat()}
    self.db.save(tender)

    dateSigned = get_now().isoformat()
    # Try set status active for main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned}},
        status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertIn("Contract signature date should be after additional awards complaint period end date",
                  response.json['errors'][0]['description'][0])

    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][0]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][2]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)
    # Try set status active for main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned}})

    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['dateSigned'], dateSigned)

# TenderMergedContracts4LotsResourceTest

def merge_four_contracts(self):
    """ Create four awards and merged them """
    awards_response = self.create_awards()
    self.active_awards(awards_response)

    # get created contracts
    contract_response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    additionalAwardIDs = [award_response.json['data']['id'] for award_response in awards_response[1:]]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], third_contract["mergedInto"])
    self.assertEqual(first_contract["id"], fourth_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(third_contract["status"], "merged")
    self.assertEqual(fourth_contract["status"], "merged")

    # Remove additionalAwardIDs
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": []}})

    self.assertEqual(response.status, '200 OK')

    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertNotIn('additionalAwardIDs', first_contract)
    self.assertNotIn('mergedInto', second_contract)
    self.assertNotIn('mergedInto', third_contract)
    self.assertNotIn('mergedInto', fourth_contract)
    self.assertNotEqual(second_contract["status"], "merged")
    self.assertNotEqual(third_contract["status"], "merged")
    self.assertNotEqual(fourth_contract["status"], "merged")


def sign_contract(self):
    """ Create four awards and merged them and sign main contracts """
    awards_response = self.create_awards()
    self.active_awards(awards_response)
    # get created contracts
    contract_response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    additionalAwardIDs = [award_response.json['data']['id'] for award_response in awards_response[1:]]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], third_contract["mergedInto"])
    self.assertEqual(first_contract["id"], fourth_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(third_contract["status"], "merged")
    self.assertEqual(fourth_contract["status"], "merged")

    # set stand still period
    tender = self.db.get(self.tender_id)
    now = get_now()
    for award in tender['awards']:
        award['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                    "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)

    # Set status active for first contract
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {'data': {'status': 'active'}})

    self.assertEqual(response.json['data']['status'], 'active')
    # and check tender status
    response = self.app.get('/tenders/{}'.format(self.tender_id))
    self.assertEqual(response.json['data']['status'], 'complete')


def cancel_award_4lot(self):
    """ Create two awards and merged them and try to cancel both """
    awards_response = self.create_awards()
    self.active_awards(awards_response)
    # get created contracts
    contract_response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    additionalAwardIDs = [award_response.json['data']['id'] for award_response in awards_response[1:]]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], third_contract["mergedInto"])
    self.assertEqual(first_contract["id"], fourth_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(third_contract["status"], "merged")
    self.assertEqual(fourth_contract["status"], "merged")

    # Cancel first additional award
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
        self.tender_id, second_contract['awardID'], self.tender_token),
        {'data': {'status': 'cancelled'}}, status=403)

    self.assertEqual(response.status, "403 Forbidden")
    self.assertEqual(response.json['errors'][0]['description'], "Can't cancel award while it is a part of merged contracts.")

    # Check main contract
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 4)
    self.assertEqual(len(response.json['data'][0]['additionalAwardIDs']), 3)

    # Cancel second additional award
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
        self.tender_id, third_contract['awardID'], self.tender_token),
         {'data': {'status': 'cancelled'}}, status=403)

    self.assertEqual(response.status, "403 Forbidden")
    self.assertEqual(response.json['errors'][0]['description'], "Can't cancel award while it is a part of merged contracts.")

    # Check main contract
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 4)
    self.assertEqual(len(response.json['data'][0]['additionalAwardIDs']), 3)

    # Cancel third additional award
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
        self.tender_id, fourth_contract['awardID'], self.tender_token),
        {'data': {'status': 'cancelled'}}, status=403)

    self.assertEqual(response.status, "403 Forbidden")
    self.assertEqual(response.json['errors'][0]['description'], "Can't cancel award while it is a part of merged contracts.")

    # Check main contract
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 4)
    self.assertEqual(len(response.json['data'][0]['additionalAwardIDs']), 3)


def cancel_main_award_4lot(self):
    """ Create two awards and merged them and then main """
    awards_response = self.create_awards()
    self.active_awards(awards_response)
    # get created contracts
    contract_response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    additionalAwardIDs = [award_response.json['data']['id'] for award_response in awards_response[1:]]

    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], third_contract["mergedInto"])
    self.assertEqual(first_contract["id"], fourth_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(third_contract["status"], "merged")
    self.assertEqual(fourth_contract["status"], "merged")

    # Cancel main award
    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
        self.tender_id, first_contract['awardID'], self.tender_token),
        {'data': {'status': 'cancelled'}})

    self.assertEqual(response.status, "200 OK")

    # Check main award
    response = self.app.get('/tenders/{}/contracts/{}?acc_token'.format(
        self.tender_id, first_contract['id'], self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(response.json['data']['status'], 'cancelled')
    self.assertNotIn('additionalAwardIDs', response.json['data'])

    # Check contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 4)
    self.assertEqual('pending', response.json['data'][1]['status'])
    self.assertEqual('pending', response.json['data'][2]['status'])
    self.assertEqual('pending', response.json['data'][3]['status'])
    self.assertNotIn('mergedInto', response.json['data'][1])
    self.assertNotIn('mergedInto', response.json['data'][2])
    self.assertNotIn('mergedInto', response.json['data'][3])

    # Check that new awards were created and have status pending
    response = self.app.get('/tenders/{}/awards?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, "200 OK")
    self.assertEqual(len(response.json['data']), 5)
    self.assertEqual(response.json['data'][-1]['status'], 'pending')


def cancel_first_main_award(self):
    awards_response = self.create_awards()
    self.active_awards(awards_response)

    # get created contracts
    contract_response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_additionalAwardIDs = [awards_response[1].json['data']['id']]
    second_additionalAwardIDs = [awards_response[3].json['data']['id']]

    # Merge contracts
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": first_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][2]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": second_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], first_additionalAwardIDs)
    self.assertEqual(third_contract["additionalAwardIDs"], second_additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(third_contract["id"], fourth_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(fourth_contract["status"], "merged")

    # Cancel first main contract

    response = self.app.patch_json('/tenders/{}/awards/{}?acc_token={}'.format(
        self.tender_id, first_contract['awardID'], self.tender_token),
        {"data": {"status": "cancelled"}}
    )

    self.assertEqual(response.status, "200 OK")

    self.assertEqual(response.json['data']['status'], 'cancelled')

    # Check rest contracts
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    self.assertEqual(response.status, '200 OK')

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract['status'], 'cancelled')
    self.assertEqual(second_contract['status'], 'pending')
    self.assertNotIn('additionalAwardIDs', first_contract)
    self.assertNotIn('mergedInto', second_contract)
    self.assertEqual(third_contract['additionalAwardIDs'], second_additionalAwardIDs)
    self.assertEqual(third_contract['status'], 'pending')
    self.assertEqual(fourth_contract['status'], 'merged')
    self.assertEqual(fourth_contract['mergedInto'], third_contract['id'])


def merge_by_two_contracts(self):
    awards_response = self.create_awards()
    self.active_awards(awards_response)

    # get created contracts
    contract_response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_additionalAwardIDs = [awards_response[1].json['data']['id']]
    second_additionalAwardIDs = [awards_response[3].json['data']['id']]

    # Merge contracts
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": first_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][2]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": second_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], first_additionalAwardIDs)
    self.assertEqual(third_contract["additionalAwardIDs"], second_additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(third_contract["id"], fourth_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(fourth_contract["status"], "merged")

    # set stand still period
    tender = self.db.get(self.tender_id)
    now = get_now()
    for award in tender['awards']:
        award['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                    "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)

    # Set status active for first contract
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, first_contract['id'], self.tender_token),
        {'data': {'status': 'active'}})

    self.assertEqual(response.json['data']['status'], 'active')
    # and check tender status, tender must have status 'active.awarded;
    response = self.app.get('/tenders/{}'.format(self.tender_id))
    self.assertNotEqual(response.json['data']['status'], 'complete')

    # set status active for first contract
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, third_contract['id'], self.tender_token),
        {'data': {'status': 'active'}})

    # and check tender status
    response = self.app.get('/tenders/{}'.format(self.tender_id))
    self.assertEqual(response.json['data']['status'], 'complete')


def try_merge_main_contract(self):
    """ Try merge contract which has additionalAwardIDs """
    awards_response = self.create_awards()
    self.active_awards(awards_response)

    # get created contracts
    contract_response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_additionalAwardIDs = [awards_response[1].json['data']['id']]

    # Merge contracts
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": first_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][2]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": [contract_response.json['data'][0]['awardID']]}},
        status=403)

    self.assertEqual(response.status, '403 Forbidden')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], first_additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertNotEqual(fourth_contract["status"], "merged")


def try_merge_contract_two_times(self):
    """ Check that we can merge contract 2 times in different contracts """
    awards_response = self.create_awards()
    self.active_awards(awards_response)

    # get created contracts
    contract_response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_additionalAwardIDs = [awards_response[1].json['data']['id']]
    second_additionalAwardIDs = [awards_response[3].json['data']['id']]

    # Merge contracts
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": first_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][2]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": second_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], first_additionalAwardIDs)
    self.assertEqual(third_contract["additionalAwardIDs"], second_additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(third_contract["id"], fourth_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(fourth_contract["status"], "merged")

    # Try merge contract which already merge
    first_additionalAwardIDs.append(awards_response[3].json['data']['id'])
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": first_additionalAwardIDs}},
        status=403)

    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'],
                     [
                         {
                             "location": "body",
                             "name": "data",
                             "description": "Can't merge contract in status merged"
                         }
                     ])

    # Remove fourth contract from second_additionalAwardIDs
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][2]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": []}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    # check fourth contract
    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertNotEqual('mergedInto', fourth_contract)
    self.assertNotEqual(fourth_contract["status"], "merged")

    # Merge fourth contract
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": first_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], first_additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(first_contract["id"], fourth_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(fourth_contract["status"], "merged")


def activate_contract_with_complaint_4lot(self):
    """" Try activate main contract while additional wards has complaints """
    awards_response = self.create_awards()
    self.active_awards(awards_response)
    # get created contracts
    contract_response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_additionalAwardIDs = [awards_response[1].json['data']['id']]
    second_additionalAwardIDs = [awards_response[3].json['data']['id']]

    # Merge contracts
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": first_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][2]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": second_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], first_additionalAwardIDs)
    self.assertEqual(third_contract["additionalAwardIDs"], second_additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(third_contract["id"], fourth_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(fourth_contract["status"], "merged")

    # Create complaint on first additional award
    bid1_token = self.db[self.tender_id]['bids'][0]['owner_token']
    response = self.app.post_json('/tenders/{}/awards/{}/complaints?acc_token={}'.format(self.tender_id, second_contract['awardID'], bid1_token),
                                  {'data': {
                                      'title': 'complaint title',
                                      'description': 'complaint description',
                                      'author': test_organization,
                                      'status': 'claim'
                                  }})
    self.assertEqual(response.status, '201 Created')
    second_award_complaint = response.json['data']
    second_award_complaint_owner_token = response.json['access']['token']

    # Create complaint on second additional award
    response = self.app.post_json(
        '/tenders/{}/awards/{}/complaints?acc_token={}'.format(self.tender_id, fourth_contract['awardID'], bid1_token),
        {'data': {
            'title': 'complaint title',
            'description': 'complaint description',
            'author': test_organization,
            'status': 'claim'
        }})
    self.assertEqual(response.status, '201 Created')
    fourth_award_complaint = response.json['data']
    fourth_award_complaint_owner_token = response.json['access']['token']

    # Update complaintPeriod for awards
    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][0]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][2]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][3]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)

    # Lets resolve first complaint
    self.edit_award_complaint(second_contract['awardID'], second_award_complaint['id'], self.tender_token,
                           {"data": {"status": "answered",
                                         "resolutionType": "resolved",
                                         "resolution": "resolution text " * 2}})

    # Lets resolve second complaint
    self.edit_award_complaint(fourth_contract['awardID'], fourth_award_complaint['id'], self.tender_token,
                           {"data": {"status": "answered",
                                     "resolutionType": "resolved",
                                     "resolution": "resolution text " * 2}
                           })

    # Try set status active for first main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": get_now().isoformat(), "status": "active"}},
        status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [{u'description': u"Can't sign contract before reviewing all complaints", u'location': u'body', u'name': u'data'}])

    # Try set status active for second main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": get_now().isoformat(), "status": "active"}},
        status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [{u'description': u"Can't sign contract before reviewing all complaints", u'location': u'body', u'name': u'data'}])

    self.edit_award_complaint(second_contract['awardID'], second_award_complaint['id'],
                           second_award_complaint_owner_token,
                           {"data": {"satisfied": True, "status": "resolved"}})

    # Try sign first main contract again
    dateSigned = get_now().isoformat()
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned, "status": "active"}})

    self.assertEqual(response.json['data']['status'], 'active')
    self.assertEqual(response.json['data']['dateSigned'], dateSigned)

    # Try set status active for second main contract again
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, third_contract['id'], self.tender_token),
        {"data": {"dateSigned": get_now().isoformat(), "status": "active"}},
        status=403)
    self.assertEqual(response.status, '403 Forbidden')
    self.assertEqual(response.json['errors'], [{u'description': u"Can't sign contract before reviewing all complaints", u'location': u'body', u'name': u'data'}])

    self.edit_award_complaint(fourth_contract['awardID'], fourth_award_complaint['id'],
                           fourth_award_complaint_owner_token,
                           {"data": {"satisfied": True, "status": "resolved"}})

    # And try sign contract again
    dateSigned = get_now().isoformat()
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, third_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned, "status": "active"}})

    self.assertEqual(response.json['data']['status'], 'active')
    self.assertEqual(response.json['data']['dateSigned'], dateSigned)


def additional_awards_dateSigned_4lot(self):
    """ Try set dateSigned before end complaint period for additional awards """
    awards_response = self.create_awards()
    self.active_awards(awards_response)
    # get created contracts
    contract_response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))
    first_additionalAwardIDs = [awards_response[1].json['data']['id']]
    second_additionalAwardIDs = [awards_response[3].json['data']['id']]

    # Merge contracts
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][0]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": first_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')
    response = self.app.patch_json('/tenders/{}/contracts/{}?acc_token={}'.format(
        self.tender_id, contract_response.json['data'][2]['id'], self.tender_token),
        {"data": {"additionalAwardIDs": second_additionalAwardIDs}})

    self.assertEqual(response.status, '200 OK')

    # Get contracts and check fields
    response = self.app.get('/tenders/{}/contracts?acc_token={}'.format(self.tender_id, self.tender_token))

    first_contract, second_contract, third_contract, fourth_contract = response.json['data']
    self.assertEqual(first_contract["additionalAwardIDs"], first_additionalAwardIDs)
    self.assertEqual(third_contract["additionalAwardIDs"], second_additionalAwardIDs)
    self.assertEqual(first_contract["id"], second_contract["mergedInto"])
    self.assertEqual(third_contract["id"], fourth_contract["mergedInto"])
    self.assertEqual(second_contract["status"], "merged")
    self.assertEqual(fourth_contract["status"], "merged")

    # Update complaintPeriod for additional award
    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][0]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now + timedelta(days=1)).isoformat(),
                                              "endDate": (now + timedelta(days=1)).isoformat()}
    tender['awards'][2]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    tender['awards'][3]['complaintPeriod'] = {"startDate": (now + timedelta(days=1)).isoformat(),
                                              "endDate": (now + timedelta(days=1)).isoformat()}
    self.db.save(tender)

    dateSigned = get_now().isoformat()
    # Try set status active for first main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned}},
        status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertIn("Contract signature date should be after additional awards complaint period end date",
                  response.json['errors'][0]['description'][0])

    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][1]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)
    # Try now set status active for first main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, first_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned}})

    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['dateSigned'], dateSigned)

    # Try set status active for second main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, third_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned}},
        status=422)
    self.assertEqual(response.status, '422 Unprocessable Entity')
    self.assertIn("Contract signature date should be after additional awards complaint period end date",
                  response.json['errors'][0]['description'][0])

    tender = self.db.get(self.tender_id)
    now = get_now()
    tender['awards'][3]['complaintPeriod'] = {"startDate": (now - timedelta(days=1)).isoformat(),
                                              "endDate": (now - timedelta(days=1)).isoformat()}
    self.db.save(tender)
    # Try set status active for main contract
    response = self.app.patch_json("/tenders/{}/contracts/{}?acc_token={}".format(
        self.tender_id, third_contract['id'], self.tender_token),
        {"data": {"dateSigned": dateSigned}})

    self.assertEqual(response.status, '200 OK')
    self.assertEqual(response.json['data']['dateSigned'], dateSigned)


