from odoo import models, fields, api, _

class NCR_Contact(models.Model):
    _inherit = 'res.partner'
    
    car_report_ids = fields.One2many('quality.car.report', 'partner_id')
    car_report_count = fields.Integer(compute='_compute_car_report_count')
    ncr_report_ids = fields.One2many('quality.ncr.report', 'partner_id')
    ncr_report_count = fields.Integer(compute='_compute_ncr_report_count')

    def _compute_ncr_report_count(self):
        for record in self:
            record.ncr_report_count = len(record.ncr_report_ids)
    
    def view_ncr_report_ids(self):
        self.ensure_one()
        ncr_reports = self.ncr_report_ids.ids
        action = {
            'res_model': 'quality.ncr.report',
            'type': 'ir.actions.act_window',
        }

        if len(ncr_reports) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': ncr_reports[0],
            })
        else:
            action.update({
                'name': _("%s Non-Conformance Reports") % self.name,
                'domain': [('id', 'in', ncr_reports)],
                'view_mode': 'tree,form',
            })
        return action

    def _compute_car_report_count(self):
        for record in self:
            record.car_report_count = len(record.car_report_ids)

    def view_car_report_ids(self):
        self.ensure_one()
        car_reports = self.car_report_ids.ids
        action = {
            'res_model': 'quality.car.report',
            'type': 'ir.actions.act_window',
        }

        if len(car_reports) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': car_reports[0],
            })
        else:
            action.update({
                'name': _("%s Corrective Action Reports") % self.name,
                'domain': [('id', 'in', car_reports)],
                'view_mode': 'tree,form',
            })
        return action
    