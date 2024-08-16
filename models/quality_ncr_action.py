# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
import datetime
from odoo.exceptions import AccessError


class QualityNonConformanceActions(models.Model):
    _name = "quality.ncr.action"
    _description = "Quality Non-Conformance Actions"
    _inherit = ["mail.thread", 'mail.activity.mixin', 'analytic.mixin', 'portal.mixin']
    _order = "name"

    analytic_account_ids = fields.Many2many('account.analytic.account', compute='_compute_analytic_account_ids', store=True)
    date_close = fields.Date(string="Close Date", store=True)
    date_open = fields.Date(string="Open Date", default=lambda self: fields.Date.today(), store=True)
    days_open = fields.Integer(compute="_compute_days_open", store=False, string="Days Open")
    name = fields.Char(string="Action Number", default="New", copy=False, store=True)
    ncr_report_id = fields.Many2one("quality.ncr.report", ondelete="cascade", string="NCR Reference", required=True)
    project_manager_ids = fields.Many2many(related="ncr_report_id.project_manager_ids", string="Project Manager")
    rework_repair_qa_employee_id = fields.Many2one("hr.employee", ondelete="restrict", string="Rework/Repair QA By", store=True)
    responsible_employee_id = fields.Many2one("hr.employee", ondelete="restrict", string="Responsible Employee", store=True)
    responsible_department_id = fields.Many2one("hr.department", ondelete="restrict", string="Responsible Department", store=True, required=True)
    responsible_department_head_id = fields.Many2one(related="responsible_department_id.manager_id", string="Responsible Department Head")
    short_description = fields.Char(string="Short Description", store=True)
    state = fields.Selection([('draft', 'New'), ('warning', 'Rework/Repair QA'), ('done', 'Completed')], default='draft', string='State', store=True, tracking=True)
    expected_condition = fields.Text(string="Suggested Actions", store=True)
    work_completed = fields.Text(string="Work Completed", store=True)
    work_instructions = fields.Text(string="Work Instructions", store=True, required=True)
    lock = fields.Boolean(compute="_compute_lock", store=True, inverse='_inverse_lock')

    @api.depends('ncr_report_id.state')
    def _compute_lock(self):
        for record in self:
            if record.ncr_report_id.state == 'closed':
                record.lock == True
            else:
                record.lock == False


    def _inverse_lock(self):
        pass

    @api.model_create_multi
    def create(self, val_list):
        ncr_actions = self.env['quality.ncr.action']
        for vals in val_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].with_user(SUPERUSER_ID).next_by_code("quality_ncr_action_seq") or "New"

            res = super(QualityNonConformanceActions, self).create(vals)

            if "responsible_employee_id" in vals:
                res.actionNotification()
            ncr_actions |= res
        return ncr_actions

    @api.depends('analytic_distribution')
    def _compute_analytic_account_ids(self):
        for record in self:
            record.analytic_account_ids = bool(record.analytic_distribution) and self.env['account.analytic.account'].browse(
                list({int(account_id) for ids in record.analytic_distribution for account_id in ids.split(",")})
            ).exists()

    def _message_log(self, *,
                     body='', subject=False,
                     author_id=None, email_from=None,
                     message_type='notification',
                     partner_ids=False,
                     attachment_ids=False, tracking_value_ids=False):
        """ Shortcut allowing to post note on a document. See ``_message_log_batch``
        for more details. """
        self.ensure_one()
        new_tracking_value_ids = []
        for tracking in tracking_value_ids:
            tracking[2]['old_value_char'] = self.name + ': ' + tracking[2]['old_value_char']
            new_tracking_value_ids.append(tracking)
        return self.ncr_report_id._message_log_batch(
            {self.ncr_report_id.id: body}, subject=subject,
            author_id=author_id, email_from=email_from,
            message_type=message_type,
            partner_ids=partner_ids,
            attachment_ids=attachment_ids, tracking_value_ids=new_tracking_value_ids
        )

    def _get_recipients_emails(self):
        return self.responsible_department_head_id.work_email + "," + self.responsible_employee_id.work_email

    def actionNotification(self):
        template_id = self.env.ref("AS9100_quality.email_template_quality_ncr_action_created")
        template_id.send_mail(self.id, force_send=True)

    @api.depends("date_close", "date_open")
    def _compute_days_open(self):
        for record in self:
            if record.date_close:
                record["days_open"] = abs((record.date_close - record.date_open).days)
            else:
                record["days_open"] = abs((datetime.date.today() - record.date_open).days)

    def _compute_access_url(self):
        super(QualityNonConformanceActions, self)._compute_access_url()
        for record in self:
            record.access_url = '/my/ncrs/actions/%s' % record.id

    def action_rework(self):
        for record in self:
            record.state = 'warning'

    def action_complete(self):
        for record in self:
            record.state = 'done'
            record.date_close = datetime.date.today()

    def action_open(self):
        for record in self:
            record.state = 'draft'
            record.date_close = False
