# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
import datetime
from odoo.exceptions import ValidationError, AccessError

class QualityNonConformanceReport(models.Model):
    _name = "quality.ncr.report"
    _description = "Quality Non-Conformance Reports"
    _inherit = ['analytic.mixin', 'quality.alert', 'portal.mixin']
    _order = "name"

    analytic_account_ids = fields.Many2many('account.analytic.account', compute='_compute_analytic_account_details', store=True)
    child_ids = fields.One2many("quality.ncr.report", "parent_id", string="Child NCRs", tracking=True)
    classification = fields.Selection([("major", "Major"), ("minor", "Minor")], string="Classification", tracking=True)
    count_child_ids = fields.Integer(compute='_compute_count_child_ids')
    count_car_report_ids = fields.Integer(compute='_compute_count_car_report_ids')
    currency_id = fields.Many2one("res.currency", string="Currency", required=True, default=lambda self: self.env.user.company_id.currency_id.id)
    date_close = fields.Date(string="Close Date", tracking=True)
    date_open = fields.Date(string="Open Date", default=lambda self: fields.Date.today(), tracking=True)
    days_open = fields.Integer(string="Days Open", store=False, compute="_compute_days_open")
    description = fields.Char(string="Is Condition", tracking=True, help="Describe the current state of the product and why it is non-conforming.")
    disposition = fields.Selection([("use", "Use-As-Is"), ("rework", "Rework"), ("repair", "Repair"), ("cause", "Cause Analysis"), ("scrap", "Scrap"), ("return", "Return to Supplier"), ("no_defect", "No Defect")], string="Disposition", tracking=True)
    disposition_text = fields.Text(tracking=True)
    expected_condition = fields.Text(string="Should Be Condition", tracking=True, help="Explain the conforming state of the part on the NCR as well as explain what can be done to get the part to that state.")
    lot_ids = fields.Many2many("stock.lot", ondelete="restrict", string="Serial/Lot Numbers", store=True, tracking=True, domain="[('product_id', '=', product_id)]")
    justification = fields.Text(string="Justification", tracking=True)
    map_number = fields.Char(string="MAP Number", tracking=True)
    name = fields.Char(string="NCR Number", tracking=True, default="New", copy=False)
    ncr_action_ids = fields.One2many("quality.ncr.action", "ncr_report_id", string="Assigned Actions")
    ncr_approval_ids = fields.One2many("quality.ncr.approvals", "ncr_report_id", string="Approvals")

    operational_area = fields.Selection([("final", "Assembly (Final)"), ("screening", "Cell Screening"), ("bending", "Cutting and Bending"), ("engineering", "Engineering"), ("inspection", "Incoming Inspection"), ("potting", "Potting"),
                                         ("soldering", "Soldering"), ("sub_assembly", "Sub-Assembly"), ("test", "Test"), ("welding", "Welding"), ("other", "Other")], string="Operational Area", tracking=True)

    parent_id = fields.Many2one("quality.ncr.report", string="Parent NCR", tracking=True, copy=False)

    problem_type = fields.Selection([("electrical_design", "Electrical Design Error"), ("mechanical_design", "Mechanical Design Error"), ("software_design", "Software Design Error"), ("process", "Process Error"), ("technician", "Technician Error"),
                                     ("test", "Test Error"), ("supplier", "Supplier Defect"), ("unknown", "To Be Determined")], string="Problem Type", tracking=True)

    product_cost = fields.Float(string="Product Cost", related="product_id.standard_price", tracking=True)
    product_id = fields.Many2one('product.product', 'Product', check_company=True, domain="[('type', 'in', ['consu', 'product'])]", required=True)
    project_manager_ids = fields.Many2many("hr.employee", compute="_compute_analytic_account_details", ondelete="restrict", string="Project Managers", store=True, tracking=True)
    purchase_order_id = fields.Many2one("purchase.order", tracking=True)
    quantity = fields.Float(string="Quantity", tracking=True)
    quality_member_check = fields.Boolean(compute="_compute_quality_member", string="Quality Member", default="False")
    reason_for_hold = fields.Text(string="Reason For Hold", tracking=True)
    responsible_employee_id = fields.Many2one("hr.employee", ondelete="restrict", string="Responsible Employee", help="Employee responsible for causing or discovering the NCR.")
    responsible_engineer_id = fields.Many2one("hr.employee", ondelete="restrict", string="Responsible Engineer", tracking=True, help="This is the Engineer responsible for this product who can assist with determining the disposition of this NCR.")
    rma_detailed_issue = fields.Text(string="RMA Detailed Issue", tracking=True)
    rma_expected_action = fields.Text(string="RMA Expected Action", tracking=True)
    state = fields.Selection([("draft", "New"), ("open", "Open"), ("reconvene", "Reconvene"), ("hold", "Hold"), ("closed", "Closed")], string="State", tracking=True, default="draft", store=True)
    total_cost = fields.Float(compute="_compute_total_cost", store=True, string="Total Cost")

    @api.model_create_multi
    def create(self, val_list):
        ncr_reports = self.env['quality.ncr.report']
        for vals in val_list:
            if vals.get("parent_id", False):
                parent_report = self.search([('id', '=', vals['parent_id'])])
                vals["name"] = parent_report.name + '-00' + str(1 + len(parent_report.child_ids))

            if vals.get("name", 'New') == "New":
                vals["name"] = self.env["ir.sequence"].with_user(SUPERUSER_ID).next_by_code("quality_ncr_report_seq")

            if "reason_for_hold" in vals and vals["reason_for_hold"]:
                vals['state'] = 'hold'

            res = super(QualityNonConformanceReport, self).create(vals)
            res._ncr_creation_notification()
            ncr_reports |= res
        return ncr_reports

    def write(self, vals):
        if "reason_for_hold" in vals and vals["reason_for_hold"]:
            vals['state'] = 'hold'
        return super(QualityNonConformanceReport, self).write(vals)

    def _compute_count_car_report_ids(self):
        for record in self:
            record.count_car_report_ids = self.env['quality.car.report'].search_count([('ncr_report_id', '=', record.id)])

    def _compute_quality_member(self):
        for record in self:
            if self.env.user.employee_id.id in self.env.ref("AS9100_quality.quality_department").member_ids.ids or self.env.user.employee_id.id in self.env.ref("AS9100_quality.quality_department").manager_id.ids:
                record.quality_member_check = True
            else:
                record.quality_member_check = False

    @api.depends('analytic_distribution')
    def _compute_analytic_account_details(self):
        for record in self:
            employee_ids = []
            analytic_account_ids = bool(record.analytic_distribution) and self.env['account.analytic.account'].browse(list({int(account_id) for ids in record.analytic_distribution for account_id in ids.split(",")})).exists()
            record.analytic_account_ids = analytic_account_ids
            projects = self.env['project.project'].search([('analytic_account_id', 'in', analytic_account_ids.ids)]) if analytic_account_ids else []
            for project in projects:
                if project.user_id:
                    if project.user_id.employee_id:
                        employee_ids.append(project.user_id.employee_id.id)
            record.project_manager_ids = employee_ids

    @api.depends('child_ids')
    def _compute_count_child_ids(self):
        for record in self:
            record.count_child_ids = len(record.child_ids)

    @api.depends("date_close", "date_open")
    def _compute_days_open(self):
        for record in self:
            date_initiated = record.date_open if record.date_open else record.create_date
            if record.state != "Closed":
                days = abs((datetime.date.today() - date_initiated).days) if date_initiated else 0
            else:
                days = abs((record.date_close - date_initiated).days) if record.date_close and date_initiated else 0

            record["days_open"] = days

    @api.depends("quantity", "product_cost")
    def _compute_total_cost(self):
        for record in self:
            record["total_cost"] = record.quantity * record.product_cost

    @api.onchange("parent_id")
    def _update_default_values(self):
        if self.parent_id.analytic_account_ids:
            self.analytic_account_ids = self.parent_id.analytic_account_ids

    @api.onchange("picking_id")
    def _get_partner(self):
        self.partner_id = self.picking_id.partner_id["id"] if self.picking_id else False

    @api.onchange("product_id")
    def _onchange_product_id(self):
        self.lot_ids = False

    def open_ncr_report(self):
        for record in self:
            if self.env.user.employee_id.id in self.env.ref("AS9100_quality.quality_department").member_ids.ids or self.env.user.employee_id.id in self.env.ref("AS9100_quality.quality_department").manager_id.ids:
                record["state"] = "open"
                record['reason_for_hold'] = False
                record['date_close'] = False
            else:
                raise AccessError(_("Only Quality Department can Open Non-Conformance Reports."))
    
    def hold_ncr_report(self):
        for record in self:
            record["state"] = "hold"

    def close_ncr_report(self):
        for record in self:
            if record.ncr_action_ids.filtered(lambda x: x.state != 'done'):
                raise ValidationError(_("This NCR has some Uncompleted actions and can not be closed till they are all done."))
            if record.ncr_approval_ids.filtered(lambda x: not x.is_approved):
                raise ValidationError(_("This NCR has not being fully approved. Please get all approvals before closing."))
            record['date_close'] = datetime.date.today()
            record["state"] = "closed"
            record.ncr_action_ids['lock'] = True

    def reset_to_draft(self):
        for record in self:
            if record.state == 'closed':
                raise ValidationError(_("This NCR has been Closed and can not be reset to New."))
            record['date_close'] = False
            record["state"] = "draft"
            record.ncr_action_ids['lock'] = False

    def reconvene_ncr_report(self):
        for record in self:
            record["state"] = "reconvene"

    def _get_opened_recipients(self):
        emails = [self.responsible_engineer_id.work_email]
        for manager in self.project_manager_ids:
            emails.append(manager.work_email)
        res = str(emails).replace("[", "").replace("]", "").replace("\"", "")
        return res

    def _get_quality_representatives_emails(self):
        emails = []
        for member in self.quality_member_ids:
            emails.append(member.work_email)
        return ",".join(emails)

    def _ncr_creation_notification(self):
        template_id = self.env.ref("AS9100_quality.email_template_quality_ncr_report_open")
        template_id.send_mail(self.id, force_send=True)

    @api.onchange('ncr_action_ids', 'ncr_action_ids.state')
    def _actions_complete_notification(self):
        if not self.ncr_action_ids.filtered(lambda x: x.state not in ('done', 'blocked')) and self.ncr_action_ids:
            template_id = self.env.ref("AS9100_quality.email_template_quality_ncr_report_actions_complete")
            template_id.send_mail(self.id, force_send=True)

    def action_view_parent(self):
        action = {
            'res_model': 'quality.ncr.report',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.parent_id.id,
        }
        return action

    def action_view_children(self):
        self.ensure_one()
        child_reports = self.child_ids.ids
        action = {
            'res_model': 'quality.ncr.report',
            'type': 'ir.actions.act_window',
            'context': {
                'default_analytic_distribution': self.analytic_distribution,
                'default_parent_id': self.parent_id.id if self.parent_id else self.id,
                'default_responsible_engineer_id': self.responsible_engineer_id.id if self.responsible_engineer_id else False,
                'default_picking_id': self.picking_id.id if self.picking_id else False,
                'default_responsible_employee_id': self.responsible_employee_id.id if self.responsible_employee_id else False,
                'default_problem_type': self.problem_type,
                'default_operational_area': self.operational_area,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
            },
        }
        if len(child_reports) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': child_reports[0],
            })
        if len(child_reports) == 0:
            action.update({
                'view_mode': 'form',
            })
        else:
            action.update({
                'name': _("%s Children Reports") % self.name,
                'domain': [('id', 'in', child_reports)],
                'view_mode': 'tree,form',
            })
        return action

    def action_view_car_reports(self):
        self.ensure_one()
        car_reports = self.env['quality.car.report'].search([('ncr_report_id', '=', self.id)]).ids
        action = {
            'res_model': 'quality.car.report',
            'type': 'ir.actions.act_window',
        }

        if len(car_reports) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': car_reports[0],
            })
        else:
            action.update({
                'name': _("%s Corrective Action Reports") % self.name,
                'domain': [('id', 'in', car_reports)],
                'view_mode': 'tree,form',
            })
        return action

    def action_view_production_order(self):
        action = {
            'res_model': 'mrp.production',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.production_id.id,
        }
        return action

    def action_view_workorder(self):
        action = {
            'res_model': 'mrp.workorder',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.workorder_id.id,
        }
        return action

    def action_view_quality_check(self):
        action = {
            'res_model': 'quality.check',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.check_id.id,
        }
        return action

    def _compute_access_url(self):
        super(QualityNonConformanceReport, self)._compute_access_url()
        for record in self:
            record.access_url = '/my/ncrs/%s' % (record.id)

    def action_preview_ncr_report(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': self.get_portal_url(),
        }