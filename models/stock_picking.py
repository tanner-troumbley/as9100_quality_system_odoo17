from odoo import models, fields, api

class stock_picking(models.Model):
    _inherit = "stock.picking"

    ncr_report_ids = fields.One2many('quality.ncr.report',  'picking_id', string="NCRs")
    ncr_report_count = fields.Integer(compute="_compute_ncr_report_count")

    def _compute_ncr_report_count(self):
        for workorder in self:
            workorder.ncr_report_count = len(workorder.ncr_report_ids)

    def open_nrc_report_picking(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("AS9100_quality.quality_ncr_report_action_window")
        action['context'] = {
            'default_company_id': self.company_id.id,
            'default_purchase_id': self.purchase_id.id if self.purchase_id else False,
            'default_picking_id': self.id,
        }
        action['domain'] = [('id', 'in', self.ncr_report_ids.ids)]
        action['views'] = [(False, 'tree'), (False, 'form')]
        if self.ncr_report_count == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.ncr_report_ids.id
        if self.ncr_report_count == 0:
            action['views'] = [(False, 'form')]
        return action