from odoo import fields, models, _


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    ncr_report_ids = fields.One2many('quality.ncr.report', "production_id", string="NCRs")
    ncr_report_count = fields.Integer(compute='_compute_ncr_report_count')

    def _compute_ncr_report_count(self):
        for production in self:
            production.ncr_report_count = len(production.ncr_report_ids)

    def button_quality_ncr_report(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("AS9100_quality.quality_ncr_report_action_window")
        action['views'] = [(False, 'form')]
        action['context'] = {
            'default_company_id': self.company_id.id,
            'default_product_id': self.product_id.id,
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id,
            'default_production_id': self.id,
            'default_analytic_distribution': self.analytic_distribution,
            'default_lot_id': self.lot_producing_id.id,
            'default_quantity': self.qty_produced,
        }
        return action

    def open_nrc_report_mrp_production(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("AS9100_quality.quality_ncr_report_action_window")
        action['context'] = {
            'default_company_id': self.company_id.id,
            'default_product_id': self.product_id.id,
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id,
            'default_production_id': self.id,
            'default_analytic_distribution': self.analytic_distribution,
            'default_lot_id': self.lot_producing_id,
            'default_quantity': self.qty_produced,
        }
        action['domain'] = [('id', 'in', self.ncr_report_ids.ids)]
        action['views'] = [(False, 'tree'), (False, 'form')]
        if self.ncr_report_count == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.ncr_report_ids.ids[0]
        if self.ncr_report_count == 0:
            action['views'] = [(False, 'form')]
        return action
