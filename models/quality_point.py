from odoo import models, fields, api, _

class Quality_Point(models.Model):
    _inherit = 'quality.check'

    ncr_report_ids = fields.One2many('quality.ncr.report', 'check_id', string='NCRs')
    ncr_report_count = fields.Integer(compute='_compute_ncr_report_count')

    def _compute_ncr_report_count(self):
        for record in self:
            record.ncr_report_count = len(record.ncr_report_ids)

    def action_see_ncr_reports(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("AS9100_quality.quality_ncr_report_action_window")
        action['context'] = {
            'check_id': self.id,
            'default_company_id': self.company_id.id,
            'default_product_id': self.product_id.id,
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id,
            'default_production_id': self.production_id.id if self.production_id else False,
            'default_analytic_distribution': self.production_id.analytic_distribution if self.production_id else False,
            'default_lot_id': self.lot_line_id,
            'default_quantity': self.qty_done,
            'default_workcenter_id': self.workcenter_id.id if self.workcenter_id else False,
            'default_workorder_id': self.workorder_id.id if self.workorder_id else False,
        }
        action['domain'] = [('id', 'in', self.ncr_report_ids.ids)]
        action['views'] = [(False, 'tree'), (False, 'form')]
        if self.ncr_report_count == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.ncr_report_ids.ids[0]
        if self.ncr_report_count == 0:
            action['views'] = [(False, 'form')]
        return action