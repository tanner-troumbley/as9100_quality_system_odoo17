# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta


class CorrectiveActionReports(models.Model):
    _name = 'quality.car.report'
    _description = 'Corrective Action Reports'
    _inherit = ["mail.thread", 'mail.activity.mixin', 'analytic.mixin']
    _order_by = 'name'

    analytic_account_ids = fields.Many2many('account.analytic.account', compute='_compute_analytic_account_ids', store=True)
    asset = fields.Char(string="Asset", help="If an asset was associated with this Corrective Action Report, put its Number here.")
    category = fields.Selection([("damage", "Damage"), ("electrical", "Design/Electrical"), ("mechanical", "Design/Mechanical"), ("software", "Design/Software"), ("process", "Process/Procedure"), ("supplier", "Supplier"), ("system", "System"), ("regulatory", "Regulatory")], string='Category', help="This is the general category of the type of problem.")
    champion_id = fields.Many2one('hr.employee', ondelete='restrict', string='Champion')
    child_ids = fields.One2many("quality.car.report", "parent_id", string="Related CARs", tracking=True)
    containment_action = fields.Text(string='Containment Action', help="Details including method used to identify containment actions. Include the amount of pieces that need to be checked and how many are affected by the problem and any related NCR Numbers.")
    car_action_ids = fields.One2many('quality.car.action', 'car_report_id', string='CAR Actions')
    car_action_corrective_ids = fields.One2many('quality.car.action', 'car_report_id', string='Corrective Actions', domain=[('type', '=', 'corrective')])
    car_action_preventative_ids = fields.One2many('quality.car.action', 'car_report_id', string="Preventative Actions", domain=[('type', '=', 'preventative')])
    corrective_action_description = fields.Text(string='Select and Verify Corrective Action', help="The action that will fix the root cause along with an explanation on how the fix will be verified.")
    corrective_action_notes = fields.Text(string='Corrective Action Notes')
    count_child_ids = fields.Integer(compute='_compute_count_child_ids')
    customer_car_reference = fields.Char(string='Customer Car Reference', help="Reference customer's internal Corrective Action Number if applicable.")
    source = fields.Selection([('internal', 'Internal'), ('customer', 'Customer'), ('supplier', 'Supplier'), ('faa', 'FAA'), ('external', "External Auditor")], string='Source of Issue', help="This is source of the CAR.", default="internal", tracking=True)
    date_close = fields.Date(string='Close Date', readonly=True, copy=False)
    date_due = fields.Date(string='ECD', default=lambda self: fields.Date.today() + relativedelta(days=30), tracking=True, help="Estimated Completion Date")
    date_initiated = fields.Date(string='Date Initiated', default=lambda self: fields.Date.today(), help="This is the date the Corrective Action Report is opened")
    days_open = fields.Integer(string='Days Open', store=True, compute='_compute_days_open')
    define_root_causes = fields.Text(string='Root Cause Definition', help="Use quality tools 5-why, to describe the root cause of the problem.")
    description = fields.Text(string='Describe Problem')
    discussion_notes = fields.Text(string="Discussion Notes", help="Any notes from finding the Root Cause. Do not include the Root Cause")
    name = fields.Char(string='Corrective Action Number', default='New', copy=False)
    ncr_report_id = fields.Many2one('quality.ncr.report', ondelete='restrict', store=True, string='NCR Reference')
    originator_id = fields.Many2one('hr.employee', ondelete='restrict', default=lambda self: self.env.user.employee_ids[0], string='Originator', help="Quality Agent assigned to the Corrective Action Report.")
    parent_id = fields.Many2one("quality.car.report", string="Parent CAR", tracking=True, copy=False)
    partner_id = fields.Many2one('res.partner', string='Customer/Supplier', help="The related customer or supplier.")
    quality_member_check = fields.Boolean(compute="_compute_quality_member", string="Quality Member")
    reason_for_hold = fields.Text(string="Reason For Hold", tracking=True, help="Person Responsible for quality.car.report")
    recurrence_prevention = fields.Text(string='Recurrence Prevention', help="Describe what steps will be taken to prevent this problem from recurring.")
    responsible_department_id = fields.Many2one("hr.department", ondelete="restrict", string="Responsible Department", tracking=True)
    responsible_department_head_id = fields.Many2one(related="responsible_department_id.manager_id", string="Responsible Department Head", tracking=True, help="This is the manager over the department that this Corrective Action Report primarily impacts or affects. (This may be the same individual as the Champion)")
    responsible_team_ids = fields.Many2many('hr.employee', relation='hr_employee_car_rel', column1='car_report_id', column2='hr_employee_id', string='Responsible Team')
    state = fields.Selection([('open', 'Open'), ('late', 'Late'), ('verification', 'Verification'), ('close', 'Closed'), ('rejected', 'Rejected'), ('hold', 'Hold')], default='open', string='State', store=True, tracking=True)
    subject = fields.Char(string='Subject', help="This field is the summary of the purpose for the Corrective Action Report.")

    @api.model_create_multi
    def create(self, val_list):
        car_reports = self.env['quality.car.report']
        for vals in val_list:
            if vals.get("parent_id", False):
                parent_report = self.search([('id', '=', vals['parent_id'])])
                vals["name"] = parent_report.name + '-00' + str(1 + len(parent_report.child_ids))

            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('quality_car_seq') or 'New'

            car_reports |= super(CorrectiveActionReports, self).create(vals)
        return car_reports

    def write(self, vals):
        if "reason_for_hold" in vals and vals["reason_for_hold"]:
            vals['state'] = 'hold'
        return super(CorrectiveActionReports, self).write(vals)

    def _compute_quality_member(self):
        for record in self:
            if self.env.user.employee_id.id in self.env.ref("AS9100_quality.quality_department").member_ids.ids or self.env.user.employee_id.id in self.env.ref("AS9100_quality.quality_department").manager_id.ids:
                record.quality_member_check = True
            else:
                record.quality_member_check = False

    @api.depends('child_ids')
    def _compute_count_child_ids(self):
        for record in self:
            record.count_child_ids = len(record.child_ids)

    @api.depends('analytic_distribution')
    def _compute_analytic_account_ids(self):
        for record in self:
            record.analytic_account_ids = bool(record.analytic_distribution) and self.env['account.analytic.account'].browse(
                list({int(account_id) for ids in record.analytic_distribution for account_id in ids.split(",")})
            ).exists()

    @api.depends('date_initiated', 'date_close', 'state')
    def _compute_days_open(self):
        for record in self:
            if record.state == "close" or record.state == 'rejected':
                days = abs((record.date_close - record.date_initiated).days)
            else:
                days = abs((datetime.date.today() - record.date_initiated).days)

            record['days_open'] = days

    @api.depends('date_initiated', 'datetime.date.today()')
    def _compute_is_late(self):
        for record in self:
            if record.date_initiated < datetime.date.today():
                record['state'] = 'late'

    def action_close_car_report(self):
        self['state'] = 'close'
        self['date_close'] = datetime.date.today()

    def action_grant_extension(self):
        self.date_due = self.date_due + relativedelta(months=1)

    def action_champion_approval(self):
        self['state'] = 'verification'

    def action_remove_hold(self):
        self['state'] = 'verification'
        self['reason_for_hold'] = False

    def action_reject_car_report(self):
        vals = {
            'analytic_distribution': self.analytic_distribution,
            'category': self.category,
            'champion_id': self.champion_id.id,
            'date_due': self.date_due + datetime.timedelta(days=7),
            'customer_car_reference': self.customer_car_reference,
            'source': self.source,
            'date_initiated': self.date_initiated,
            'description': self.description,
            'ncr_report_id': self.ncr_report_id.id,
            'originator_id': self.originator_id.id,
            'parent_id': self.parent_id.id if self.parent_id else self.id,
            'responsible_department_id': self.responsible_department_id.id,
            'responsible_team_ids': self.responsible_team_ids.ids,
            'subject': self.subject,
            'supplier_issue': self.supplier_issue,
            'partner_id': self.partner_id.id

        }
        res = self.create(vals)
        self.write({'state': 'rejected', 'date_close': datetime.date.today(), 'child_ids': [(4, res.id)]})
        return res

    def _check_champion_verification(self):
        upcoming = datetime.date.today() + relativedelta(days=5)
        car_reports = self.env['quality.car.report'].search([('date_due', '<=', upcoming), ('state', '=', 'open')])
        for report in car_reports:
            template_id = self.env.ref('AS9100_quality.mail_template_champion_verification_due')
            template_id.send_mail(report.id, force_send=True)

    def _get_quality_representatives_emails(self):
        quality_members = self.env["hr.department"].search([("xml_id", "=", "AS9100_quality.quality_department")]).member_ids
        emails = []
        for member in quality_members:
            emails.append(member.work_email)
        return ",".join(emails)

    def _check_quality_verification(self):
        upcoming = datetime.date.today() + relativedelta(days=5)
        car_reports = self.env['quality.car.report'].search([('date_due', '<=', upcoming), ('state', '=', 'verification')])

        for report in car_reports:
            template_id = self.env.ref('AS9100_quality.mail_template_quality_verification_due')
            template_id.send_mail(report.id)

    def action_view_parent(self):
        action = {
            'res_model': 'quality.car.report',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.parent_id.id,
        }
        return action

    def action_view_ncr_report(self):
        action = {
            'res_model': 'quality.ncr.report',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': self.ncr_report_id.id,
            'context': {
                'default_analytic_distribution': self.analytic_distribution,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
            },
        }
        return action

    def action_view_children(self):
        self.ensure_one()
        child_reports = self.child_ids.ids
        action = {
            'res_model': 'quality.car.report',
            'type': 'ir.actions.act_window',
            'context': {
                'default_analytic_distribution': self.analytic_distribution,
                'default_category': self.category,
                'default_responsible_department_id': self.responsible_department_id.id if self.responsible_department_id else False,
                'default_customer_car_reference': self.customer_car_reference,
                'default_source': self.source,
                'default_supplier_issue': self.supplier_issue,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_parent_id': self.parent_id.id if self.parent_id else self.id,
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
