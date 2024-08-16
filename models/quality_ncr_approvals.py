# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class QualityNonConformanceApprovals(models.Model):
    _name = 'quality.ncr.approvals'
    _description = 'Quality Non-Conformance Approvals'

    approval_type = fields.Selection([("assurance", "Quality Assurance"), ("pm", "Program Manager"), ("re", "RE"), ("pm_re", "PM/RE"), ("financial", "Financial"), ("rework", "Rework QA"), ("operations", "Operations")], string='Approval Type')
    approved_by_id = fields.Many2one('hr.employee', string="Approved By ID", compute='_compute_approved_by_id', store=True)
    is_approved = fields.Boolean(string='Approved')
    ncr_report_id = fields.Many2one('quality.ncr.report', string='NCR Reference', ondelete="cascade", required=True)
    state = fields.Selection(related='ncr_report_id.state')

    @api.model_create_multi
    def create(self, val_list):
        ncr_approvals = self.env['quality.ncr.approvals']
        for vals in val_list:
            if vals.get('is_approved', False):
                vals['approved_by_id'] = self.env.user.employee_id.id
            ncr_approvals |= super(QualityNonConformanceApprovals, self).create(vals)
        return ncr_approvals

    @api.depends('is_approved')
    def _compute_approved_by_id(self):
        for record in self:
            if record.is_approved:
                record.approved_by_id = record.env.user.employee_id
            else:
                record.approved_by_id = False
