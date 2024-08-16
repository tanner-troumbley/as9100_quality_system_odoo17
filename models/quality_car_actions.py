# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime

class CorrectiveActionReportActions(models.Model):
    _name = 'quality.car.action'
    _description = 'Corrective Action Report Actions'

    description = fields.Text(string='Action Description', store=True)
    car_report_id = fields.Many2one('quality.car.report', ondelete='Cascade', string='CAR Reference', store=True)
    date_complete = fields.Date(string='Date Complete', store=True)
    due_date = fields.Date(string='Due Date', store=True)
    name = fields.Char(string='Name', copy=False, store=True)
    responsible_employee_id = fields.Many2one('hr.employee', ondelete='set null', string='Responsible Employee', store=True)
    state = fields.Selection([('open', 'Open'), ('blocked', 'Rejected'), ('done', 'Complete')], store=True)
    type = fields.Selection([("corrective", "Corrective"), ("preventative", "Preventative")], string="Type", store=True)

    @api.onchange('state')
    def _onchange_state(self):
        if self.state == 'complete':
            self['date_complete'] = datetime.date.today()
        else:
            self['date_complete'] = False