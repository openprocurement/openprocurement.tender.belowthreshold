# -*- coding: utf-8 -*-
from openprocurement.api.utils import (
    json_view,
    context_unpack,
    APIResource,
    get_now,
    raise_operation_error
)

from openprocurement.tender.core.utils import (
    save_tender, optendersresource, apply_patch,
)

from openprocurement.tender.belowthreshold.utils import (
    add_next_award
)

from openprocurement.tender.core.validation import (
    validate_cancellation_data,
    validate_patch_cancellation_data,
)


@optendersresource(name='belowThreshold:Tender Cancellations',
                   collection_path='/tenders/{tender_id}/cancellations',
                   path='/tenders/{tender_id}/cancellations/{cancellation_id}',
                   procurementMethodType='belowThreshold',
                   description="Tender cancellations")
class TenderCancellationResource(APIResource):

    def cancel_tender(self):
        tender = self.request.validated['tender']
        if tender.status in ['active.tendering', 'active.auction']:
            tender.bids = []
        tender.status = 'cancelled'

    def cancel_lot(self, cancellation=None):
        if not cancellation:
            cancellation = self.context
        tender = self.request.validated['tender']
        [setattr(i, 'status', 'cancelled') for i in tender.lots if i.id == cancellation.relatedLot]
        statuses = set([lot.status for lot in tender.lots])
        if statuses == set(['cancelled']):
            self.cancel_tender()
        elif not statuses.difference(set(['unsuccessful', 'cancelled'])):
            tender.status = 'unsuccessful'
        elif not statuses.difference(set(['complete', 'unsuccessful', 'cancelled'])):
            tender.status = 'complete'
        if tender.status == 'active.auction' and all([
            i.auctionPeriod and i.auctionPeriod.endDate
            for i in self.request.validated['tender'].lots
            if i.numberOfBids > 1 and i.status == 'active'
        ]):
            add_next_award(self.request)

    def validate_cancellation(self, operation):
        """ TODO move validators
        This class is inherited in openua, openeu, limited packages, but validate_cancellation function has different validators.
        For now, we have no way to use different validators on methods according to procedure type.
        """
        tender = self.request.validated['tender']
        if tender.status in ['complete', 'cancelled', 'unsuccessful']:
            raise_operation_error(self.request, 'Can\'t {} cancellation in current ({}) tender status'.format(operation, tender.status))
        cancellation = self.request.validated['cancellation']
        cancellation.date = get_now()
        if any([i.status != 'active' for i in tender.lots if i.id == cancellation.relatedLot]):
            raise_operation_error(self.request, 'Can {} cancellation only in active lot status'.format(operation))
        awards_id = [
            i.id for i in tender.awards if i.lotID == cancellation.relatedLot
        ] if tender.get('awards') else False
        if cancellation.get('relatedLot') and [
            c for c in tender.get('contracts') if c.awardID in awards_id and c.status == 'merged'
        ]:
            raise_operation_error(
                self.request, 'Can {} cancellation on lot if corresponding contract is merged.'.format(operation)
            )
        return True

    @json_view(content_type="application/json", validators=(validate_cancellation_data,), permission='edit_tender')
    def collection_post(self):
        """Post a cancellation
        """
        if not self.validate_cancellation('add'):
            return
        cancellation = self.request.validated['cancellation']
        cancellation.date = get_now()
        if cancellation.relatedLot and cancellation.status == 'active':
            self.cancel_lot(cancellation)
        elif cancellation.status == 'active':
            self.cancel_tender()
        self.request.context.cancellations.append(cancellation)
        if save_tender(self.request):
            self.LOGGER.info('Created tender cancellation {}'.format(cancellation.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_cancellation_create'}, {'cancellation_id': cancellation.id}))
            self.request.response.status = 201
            self.request.response.headers['Location'] = self.request.route_url('{}:Tender Cancellations'.format(self.request.validated['tender'].procurementMethodType), tender_id=self.request.validated['tender_id'], cancellation_id=cancellation.id)
            return {'data': cancellation.serialize("view")}

    @json_view(permission='view_tender')
    def collection_get(self):
        """List cancellations
        """
        return {'data': [i.serialize("view") for i in self.request.validated['tender'].cancellations]}

    @json_view(permission='view_tender')
    def get(self):
        """Retrieving the cancellation
        """
        return {'data': self.request.validated['cancellation'].serialize("view")}

    @json_view(content_type="application/json", validators=(validate_patch_cancellation_data,), permission='edit_tender')
    def patch(self):
        """Post a cancellation resolution
        """
        if not self.validate_cancellation('update'):
            return
        apply_patch(self.request, save=False, src=self.request.context.serialize())
        if self.request.context.relatedLot and self.request.context.status == 'active':
            self.cancel_lot()
        elif self.request.context.status == 'active':
            self.cancel_tender()
        if save_tender(self.request):
            self.LOGGER.info('Updated tender cancellation {}'.format(self.request.context.id),
                        extra=context_unpack(self.request, {'MESSAGE_ID': 'tender_cancellation_patch'}))
            return {'data': self.request.context.serialize("view")}
