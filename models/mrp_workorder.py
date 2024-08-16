from odoo import fields, models, _

class MrpProductionWorkcenterLine(models.Model):
    _inherit = "mrp.workorder"

    ncr_report_ids = fields.One2many('quality.ncr.report', 'workorder_id', string="NCRs")
    ncr_report_count = fields.Integer(compute="_compute_ncr_report_count")

    def _compute_ncr_report_count(self):
        for workorder in self:
            workorder.ncr_report_count = len(workorder.ncr_report_ids)

    def button_ncr_report(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("AS9100_quality.quality_ncr_report_action_window")
        action['target'] = 'new'
        action['views'] = [(False, 'form')]
        action['context'] = {
            'default_company_id': self.company_id.id,
            'default_product_id': self.product_id.id,
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id,
            'default_workorder_id': self.id,
            'default_production_id': self.production_id.id,
            'default_analytic_distribution': self.production_id.analytic_distribution,
            'default_lot_id': self.lot_id.id,
            'default_quantity': self.qty_produced,
            'default_workcenter_id': self.workcenter_id.id,
            'discard_on_footer_button': True,
        }
        return action

    def view_nrc_reports(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("AS9100_quality.quality_ncr_report_action_window")
        action['context'] = {
            'default_analytic_distribution': self.production_id.analytic_distribution if self.production_id else False,
            'default_company_id': self.company_id.id,
            'default_lot_id': self.lot_id.id if self.lot_id else False,
            'default_product_id': self.product_id.id if self.product_id else False,
            'default_product_tmpl_id': self.product_id.product_tmpl_id.id if self.product_id else False,
            'default_production_id': self.production_id.id if self.production_id else False,
            'default_quantity': self.qty_produced,
            'default_workcenter_id': self.workcenter_id.id if self.workcenter_id else False,
            'default_workorder_id': self.id,
        }
        action['domain'] = [('id', 'in', self.ncr_report_ids.ids)]
        action['views'] = [(False, 'tree'), (False, 'form')]
        if self.ncr_report_count == 1:
            action['views'] = [(False, 'form')]
            action['res_id'] = self.ncr_report_ids.ids[0]
        if self.ncr_report_count == 0:
            action['views'] = [(False, 'form')]

        return action