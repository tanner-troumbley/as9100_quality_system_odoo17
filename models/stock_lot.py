from odoo import fields, models


class ProductionLot(models.Model):
    _inherit = 'stock.lot'

    ncr_report_count = fields.Integer(compute='_compute_quality_ncr_report_qty', groups='quality.group_quality_user')

    def _compute_quality_ncr_report_qty(self):
        for prod_lot in self:
            prod_lot.ncr_report_count = self.env['quality.ncr.report'].search_count([
                ('lot_ids', 'ilike', prod_lot.id),
                ('company_id', '=', self.env.company.id)
            ])

    def action_lot_open_quality_ncr_reports(self):
        action = self.env["ir.actions.act_window"]._for_xml_id("AS9100_quality.quality_ncr_report_action_window")
        action.update({
            'domain': [('lot_ids', 'ilike', self.id)],
            'context': {
                'default_product_id': self.product_id.id,
                'default_lot_id': self.id,
                'default_company_id': self.company_id.id,
            },
        })
        action['views'] = [(False, 'tree'), (False, 'form')]
        if self.ncr_report_count == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.env['quality.ncr.report'].search([('lot_ids', 'ilike', self.id)]).ids[0]
        if self.ncr_report_count == 0:
            action['views'] = [(False, 'form')]
        return action