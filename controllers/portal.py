import base64
from collections import OrderedDict
import ast
from datetime import datetime

from odoo import http, SUPERUSER_ID
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request, Response
from odoo.tools import image_process
from odoo.tools.translate import _
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class QualityPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        NCR = request.env['quality.ncr.report']
        if 'ncr_count' in counters:
            values['ncr_count'] = NCR.search_count([
                ('state', '!=', ['closed']), "|", "|", "|", "|", "|",
                ("responsible_employee_id", "=", request.env.user.employee_id.id),
                ("responsible_engineer_id", "=", request.env.user.employee_id.id),
                ("ncr_action_ids.responsible_employee_id", "=", request.env.user.employee_id.id),
                ("partner_id", "=", request.env.user.partner_id.id),
                ("ncr_action_ids.responsible_department_head_id", "=", request.env.user.employee_id.id),
                ("create_uid", "=", request.env.user.id)
            ]) if NCR.check_access_rights('read', raise_exception=False) else 0
        return values

    def _get_ncr_report_searchbar_sortings(self):
        return {
            'date': {'label': _('Oldest'), 'ncr_report': 'date_open asc'},
            'state': {'label': _('State'), 'ncr_report': 'state'},
            'name': {'label': _('Name'), 'ncr_report': 'name asc, id asc'},
        }

    def _ncr_report_get_page_view_values(self, ncr_report, access_token, **kwargs):
        #
        def resize_to_48(source):
            if not source:
                source = request.env['ir.binary']._placeholder()
            else:
                source = base64.b64decode(source)
            return base64.b64encode(image_process(source, size=(48, 48)))

        values = {
            'ncr_report': ncr_report,
            'resize_to_48': resize_to_48,
            'report_type': 'html',
        }
        history = 'my_ncr_history'
        return self._get_page_view_values(ncr_report, access_token, values, history, False, **kwargs)

    def _ncr_action_get_page_view_values(self, ncr_action, access_token, **kwargs):
        #
        def resize_to_48(source):
            if not source:
                source = request.env['ir.binary']._placeholder()
            else:
                source = base64.b64decode(source)
            return base64.b64encode(image_process(source, size=(48, 48)))

        values = {
            'ncr_action': ncr_action,
            'resize_to_48': resize_to_48,
            'report_type': 'html',
        }
        history = 'my_ncr_history'
        return self._get_page_view_values(ncr_action, access_token, values, history, False, **kwargs)

    @http.route(['/my/ncrs', '/my/ncrs/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_ncr_reports(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, search=None,
                              search_in='Name', **kw):
        values = self._prepare_portal_layout_values()

        NCR = request.env['quality.ncr.report']
        domain = ["|", ('state', '!=', 'closed')]

        if date_begin and date_end:
            domain += [('date_open', '>', date_begin), ('date_open', '<=', date_end)]

        if request.env.user.employee_id:
            domain += ["|", "|", "|", "|", "|", ("partner_id", "=", request.env.user.partner_id.id),
                       ("create_uid", "=", request.env.user.id),
                       ("responsible_employee_id", "=", request.env.user.employee_id.id),
                       ("responsible_engineer_id", "=", request.env.user.employee_id.id),
                       ("ncr_action_ids.responsible_employee_id", "=", request.env.user.employee_id.id),
                       ("ncr_action_ids.responsible_department_head_id", "=", request.env.user.employee_id.id)]
        else:
            domain += ["|", ("partner_id", "=", request.env.user.partner_id.id),
                       ("create_uid", "=", request.env.user.id)]

        searchbar_sortings = self._get_ncr_report_searchbar_sortings()
        # default sort
        if not sortby:
            sortby = 'name'
        order = searchbar_sortings[sortby]['ncr_report']

        # count for pager
        count = NCR.search_count(domain)

        # make pager
        pager = portal_pager(
            url="/my/ncr_report",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=count,
            page=page,
            step=self._items_per_page
        )

        # search the NCR Reports to display, according to the pager data
        ncr_reports_list = NCR.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        searchbar_inputs = {
            'Name': {'label': 'Name', 'input': 'Name', 'domain': [('name', 'like', search)]},
            'Product': {'label': 'Product', 'input': 'Product',
                        'domain': ['|', '|', ('product_id.default_code', 'like', search),
                                   ('product_id.name', 'like', search), ('product_id.barcode', 'like', search)]},
        }
        search_domain = searchbar_inputs[search_in]['domain']
        ncr_reports = ncr_reports_list.search(search_domain)
        request.session['my_ncr_history'] = ncr_reports.ids[:100]

        values.update({
            'date': date_begin,
            'ncr_reports': ncr_reports,
            'page_name': 'ncrs',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': {},
            'filterby': filterby,
            'default_url': "/my/ncr_report",
            'search': search,
            'search_in': search_in,
            'searchbar_inputs': searchbar_inputs,
        })
        page_values = kw | values
        return request.render("AS9100_quality.portal_my_ncr_reports", page_values)

    @http.route(['/my/ncrs/<int:ncr_id>'], type='http', auth="user", website=True, methods=['GET'])
    def portal_my_ncr_report(self, ncr_id=None, access_token=None, **kw):
        try:
            ncr_sudo = self._document_check_access('quality.ncr.report', ncr_id, access_token=access_token)
            if ncr_sudo.state == 'closed':
                raise AccessError('NCR Report is closed')
        except (AccessError, MissingError):
            return request.redirect('/my')

        report_type = kw.get('report_type')
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=ncr_sudo, report_type=report_type,
                                     report_ref='AS9100_quality.report_quality_ncr_report', download=kw.get('download'))

        values = self._ncr_report_get_page_view_values(ncr_sudo, access_token, **kw)
        values.update({
            'disposition': request.env.ref('AS9100_quality.field_quality_ncr_report__disposition').with_user(SUPERUSER_ID).selection_ids,
            'classification': request.env.ref('AS9100_quality.field_quality_ncr_report__classification').with_user(SUPERUSER_ID).selection_ids,
            'current_employee_id': request.env.user.employee_id,
            'message_post_hash': ncr_sudo._sign_token(request.env.user.partner_id.id),
            'message_post_pid': request.env.user.partner_id.id,
        })
        if ncr_sudo.company_id:
            values['res_company'] = ncr_sudo.company_id

        return request.render("AS9100_quality.portal_my_ncr_report", values)

    @http.route(['/my/ncrs/<int:ncr_id>/action/<int:action_id>'], type='http', auth="user", website=True,
                methods=['GET'])
    def portal_my_ncr_action(self, ncr_id=None, action_id=None, access_token=None, **kw):
        try:
            ncr_action_sudo = self._document_check_access('quality.ncr.action', action_id, access_token=access_token)
            ncr_sudo = self._document_check_access('quality.ncr.report', ncr_id, access_token=access_token)
            if ncr_sudo.state == 'closed':
                raise ValueError('NCR Report is closed')

        except (AccessError, MissingError):
            return request.redirect(f"/my/ncrs/{ncr_id}")
        except ValueError:
            return request.redirect('/my')

        values = self._ncr_action_get_page_view_values(ncr_action_sudo, access_token, **kw)
        values['employees'] = request.env['hr.employee.public'].search([])
        values['current_employee_id'] = request.env.user.employee_id
        return request.render("AS9100_quality.portal_ncr_action", values)

    @http.route(['/my/ncrs/<int:ncr_id>/create/action'], type='http', auth="user", website=True,
                methods=["POST", "GET"])
    def portal_new_ncr_action(self, ncr_id=None, access_token=None, **kw):

        try:
            ncr_sudo = self._document_check_access('quality.ncr.report', ncr_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect(f"/my/ncrs")

        values = {
            'employees': request.env['hr.employee.public'].with_user(SUPERUSER_ID).search([]),
            'departments': request.env['hr.department'].with_user(SUPERUSER_ID).search([]),
            'page_name': 'new_ncr_action',
            'source_ncr': ncr_sudo
        }

        if request.httprequest.method == "POST":
            action = request.env['quality.ncr.action'].create({"ncr_report_id": ncr_id,
                                                                                       "responsible_department_id": int(kw.get("responsible_department_id")) if kw.get("responsible_department_id") != "False" else False,
                                                                                       "responsible_employee_id": int(kw.get("responsible_employee_id")) if kw.get( "responsible_employee_id") != "False" else False,
                                                                                       "rework_repair_qa_employee_id": int(kw.get("rework_repair_qa_employee_id")) if kw.get("rework_repair_qa_employee_id") != "False" else False,
                                                                                       "short_description": kw.get("short_description"),
                                                                                       "work_instructions": kw.get("work_instructions"),
                                                                                       "expected_condition": kw.get("expected_condition"),
                                                                                       })
            return request.redirect(f"/my/ncrs/{ncr_id}/action/{action.id}")

        return request.render("AS9100_quality.portal_create_ncr_action", values)

    def _convert_analytic_account_ids(self, analytic_accounts):
        analytic_distribution = {}
        for i in analytic_accounts:
            analytic_distribution[i] = (1 / len(analytic_accounts)) * 100
        return analytic_distribution

    def _check_lots(self, lot_list, product_id):
        msg = ""
        for record in lot_list:
            lot = request.env['stock.lot'].with_user(SUPERUSER_ID).search([('id', '=', record)])
            if lot.product_id.id != product_id:
                msg += f"{lot.name}\n"

        if msg:
            raise ValidationError(_("The Following Serial/Lots Do not match the product chosen:\n" + msg))
        return lot_list

    @http.route(['/my/create/ncr'], type='http', auth="user", website=True, methods=["POST", "GET"])
    def portal_new_ncr_report(self, **kw):
        if request.httprequest.method == "POST":
            values = {"analytic_distribution": self._convert_analytic_account_ids(
                request.httprequest.form.getlist('analytic_account_ids')),
                "responsible_engineer_id": int(kw.get("responsible_engineer_id")),
                "responsible_employee_id": int(kw.get("responsible_employee_id")),
                "problem_type": kw.get("problem_type"),
                "operational_area": kw.get("operational_area"),
                "partner_id": int(kw.get("partner_id")) if kw.get("partner_id") else False,
                "map_number": kw.get("map_number"),
                "expected_condition": kw.get("expected_condition"),
                "description": kw.get("description"),
                "product_id": int(kw.get("product_id")),
                "quantity": kw.get("quantity"),
                "workcenter_id": int(kw.get("workcenter_id")) if kw.get("workcenter_id") else False,
                "purchase_order_id": int(kw.get("purchase_order_id")) if kw.get("purchase_order_id") else False,
            }

            if request.httprequest.form.getlist('lot_ids') and values['product_id']:
                values["lot_ids"] = self._check_lots(list(map(int, request.httprequest.form.getlist('lot_ids'))),
                                                     values['product_id'])

            report = request.env['quality.ncr.report'].create(values)
            return request.redirect(f"/my/ncrs/{report.id}")

        values = {
            'employees': request.env['hr.employee.public'].with_user(SUPERUSER_ID).search([]),
            'analytic_accounts': request.env['account.analytic.account'].with_user(SUPERUSER_ID).search([]),
            'problem_types': request.env.ref('AS9100_quality.field_quality_ncr_report__problem_type').with_user(SUPERUSER_ID).selection_ids,
            'operational_areas': request.env.ref('AS9100_quality.field_quality_ncr_report__operational_area').with_user(SUPERUSER_ID).selection_ids,
            'partners': request.env['res.partner'].with_user(SUPERUSER_ID).search([]),
            'products': request.env['product.product'].with_user(SUPERUSER_ID).search([('type', 'in', ('consu', 'product'))]),
            'workcenters': request.env['mrp.workcenter'].with_user(SUPERUSER_ID).search([]),
            'purchase_records': request.env['purchase.order'].with_user(SUPERUSER_ID).search([('state', 'in', ('purchase', 'done'))]),
            'page_name': 'new_ncr_report',
        }

        return request.render("AS9100_quality.portal_create_ncr_report", values)
