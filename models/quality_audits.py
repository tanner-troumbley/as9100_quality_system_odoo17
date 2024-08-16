from odoo import models, fields, api, _
import datetime
from dateutil.relativedelta import relativedelta


class Audits(models.Model):
    _name = 'quality.audit'
    _description = 'Audit'
    _inherit = ["mail.thread", 'mail.activity.mixin', 'analytic.mixin']
    _order_by = 'name'

    auditor_employee_id = fields.Many2one("hr.employee", ondelete="restrict", string="Auditor", help="Employee responsible for doing the Audit.")
    date_close = fields.Date(string='Date Closed', readonly=True, copy=False)
    date_due = fields.Date(string='Due Date', default=datetime.date.today() + relativedelta(weeks=2), help="This is the date the Audit is due.")
    date_open = fields.Date(string='Date Opened', default=datetime.date.today(), help="This is the date the Audit is opened")
    days_open = fields.Integer(string='Days Open', store=True, compute='_compute_days_open')
    name = fields.Char(string='Audit', default='New', copy=False)
    partner_id = fields.Many2one('res.partner', string='Auditee', help="The Entity requesting an Audit.")
    reason = fields.Selection([('annual', 'Regular'), ('poor', 'Poor Performance'), ('other', 'Other')], default='annual', string='Reason', store=True, tracking=True)
    state = fields.Selection([('open', 'Open'), ('late', 'Late'), ('close', 'Closed')], default='open', string='State', store=True, compute='_compute_state')
    subject = fields.Char(string='Subject')
    type = fields.Selection([('supplier', 'Supplier'), ('qms', 'QMS'), ('other', 'Other')], string='Type', store=True, tracking=True)
    description = fields.Text(string='Audit Summary')
    line_ids = fields.One2many('quality.audit.line', 'audit_id', string='Audit Actions')

    @api.model_create_multi
    def create(self, val_list):
        audits = self.env['quality.audit']
        for vals in val_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('quality_audit_seq') or 'New'

            audits |= super(Audits, self).create(vals)
        return audits

    @api.depends('date_open', 'date_close', 'state')
    def _compute_days_open(self):
        for record in self:
            if record.state == "close":
                days = abs((record.date_close - record.date_open).days)
            else:
                days = abs((datetime.date.today() - record.date_open).days)

            record['days_open'] = days

    @api.depends('date_initiated', 'datetime.date.today()')
    def _compute_is_late(self):
        for record in self:
            if record.date_initiated < datetime.date.today():
                record['state'] = 'late'

    @api.depends('line_ids', 'line_ids.state', 'date_due')
    def _compute_state(self):
        for record in self:
            state = 'open'
            if len(record.line_ids.filtered(lambda x: x.state == 'done' or x.state == 'blocked')) == len(record.line_ids):
                state = 'close'
                record.date_close = datetime.date.today()
            if record.date_due < datetime.date.today() and not record.date_close:
                state = 'late'
            record.state = state

class AuditLines(models.Model):
    _name = 'quality.audit.line'
    _description = 'Audit Action'
    _order_by = 'id'

    audit_id = fields.Many2one('quality.audit', ondelete='Cascade', string='Audit')
    description = fields.Text(string='Description')
    date_close = fields.Date(string='Close Date', readonly=True, copy=False)
    date_open = fields.Date(string='Due Date', default=datetime.date.today(), help="This is the date the Audit is opened")
    days_open = fields.Integer(string='Days Open', store=True, compute='_compute_days_open')
    name = fields.Char(string='Title', default='New', copy=False)
    state = fields.Selection([('new', 'Open'), ('done', 'Done'), ('blocked', 'Failed')], default='new', string='State', store=True)
    partner_id = fields.Many2one('res.partner', string='Assigned Entity', help="The Entity responsible for the Audit Action.")

    @api.onchange('state')
    def _onchange_state(self):
        if self.state == "blocked" or self.state == "done":
            self['date_close'] = datetime.date.today()
        else:
            self['date_close'] = False

    @api.onchange('date_open', 'state')
    def _compute_days_open(self):
        for record in self:
            if record.state == "blocked" or record.state == "done" and record.date_close:
                days = abs((record.date_close - record.date_open).days)
            else:
                days = abs((datetime.date.today() - record.date_open).days)

            record['days_open'] = days


