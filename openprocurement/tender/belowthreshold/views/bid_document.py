# -*- coding: utf-8 -*-
from openprocurement.api.models import get_now
from openprocurement.api.utils import (
    get_file,
    upload_file,
    update_file_content_type,
    json_view,
    context_unpack,
    APIResource,
)
from openprocurement.api.validation import (
    validate_file_update,
    validate_file_upload,
    validate_patch_document_data
)

from openprocurement.tender.core.utils import (
    save_tender, optendersresource, apply_patch,
)

from openprocurement.tender.core.validation import validate_bid_document_operation_period

from openprocurement.tender.belowthreshold.validation import (
    validate_view_bid_document,
    validate_bid_document_operation_with_not_pending_award,
    validate_bid_document_operation_in_not_allowed_tender_status
)


@optendersresource(name='belowThreshold:Tender Bid Documents',
                   collection_path='/tenders/{tender_id}/bids/{bid_id}/documents',
                   path='/tenders/{tender_id}/bids/{bid_id}/documents/{document_id}',
                   procurementMethodType='belowThreshold',
                   description="Tender bidder documents")
class TenderBidDocumentResource(APIResource):

    @json_view(permission='view_tender', validators=(validate_view_bid_document,))
    def collection_get(self):
        """Tender Bid Documents List"""
        if self.request.params.get('all', ''):
            collection_data = [i.serialize("view") for i in self.context.documents]
        else:
            collection_data = sorted(dict([
                (i.id, i.serialize("view"))
                for i in self.context.documents
            ]).values(), key=lambda i: i['dateModified'])
        return {'data': collection_data}

    @json_view(validators=(validate_file_upload, validate_bid_document_operation_in_not_allowed_tender_status, validate_bid_document_operation_period,
               validate_bid_document_operation_with_not_pending_award,), permission='edit_bid')
    def collection_post(self):
        """Tender Bid Document Upload
        """
        document = upload_file(self.request)
        self.context.documents.append(document)
        if self.request.validated['tender_status'] == 'active.tendering':
            self.request.validated['tender'].modified = False
        if save_tender(self.request):
            self.LOGGER.info('Created tender bid document {}'.format(document.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_bid_document_create'}, {'document_id': document.id}))
            self.request.response.status = 201
            document_route = self.request.matched_route.name.replace("collection_", "")
            self.request.response.headers['Location'] = self.request.current_route_url(_route_name=document_route, document_id=document.id, _query={})
            return {'data': document.serialize("view")}

    @json_view(permission='view_tender', validators=(validate_view_bid_document,))
    def get(self):
        """Tender Bid Document Read"""
        if self.request.params.get('download'):
            return get_file(self.request)
        document = self.request.validated['document']
        document_data = document.serialize("view")
        document_data['previousVersions'] = [
            i.serialize("view")
            for i in self.request.validated['documents']
            if i.url != document.url
        ]
        return {'data': document_data}

    @json_view(validators=(validate_file_update, validate_bid_document_operation_in_not_allowed_tender_status, validate_bid_document_operation_period,
               validate_bid_document_operation_with_not_pending_award,), permission='edit_bid')
    def put(self):
        """Tender Bid Document Update"""
        document = upload_file(self.request)
        self.request.validated['bid'].documents.append(document)
        if self.request.validated['tender_status'] == 'active.tendering':
            self.request.validated['tender'].modified = False
        if save_tender(self.request):
            self.LOGGER.info('Updated tender bid document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_bid_document_put'}))
            return {'data': document.serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_document_data, validate_bid_document_operation_in_not_allowed_tender_status, validate_bid_document_operation_period,
               validate_bid_document_operation_with_not_pending_award,), permission='edit_bid')
    def patch(self):
        """Tender Bid Document Update"""
        if self.request.validated['tender_status'] == 'active.tendering':
            self.request.validated['tender'].modified = False
        if apply_patch(self.request, src=self.request.context.serialize()):
            update_file_content_type(self.request)
            self.LOGGER.info('Updated tender bid document {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_bid_document_patch'}))
            return {'data': self.request.context.serialize("view")}
