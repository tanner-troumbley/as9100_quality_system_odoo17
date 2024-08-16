from odoo import api, fields, models, _


class quality_car_report_wizard(models.TransientModel):
    _name = 'quality.car.report.wizard'
    _description = 'Corrective Action Report Wizard'
    _inherit = ['analytic.mixin']

    champion_id = fields.Many2one('hr.employee')
    description = fields.Text(string='Describe Problem')
    ncr_report_id = fields.Many2one('quality.ncr.report', string='NCR Reference')
    responsible_department_id = fields.Many2one("hr.department", ondelete="restrict", string="Responsible Department")
    subject = fields.Char(string='Subject Line')
    responsible_team_ids = fields.Many2many('hr.employee', relation='hr_employee_car_wizard_rel', column1='car_wizard_id', column2='hr_employee_id', string='Responsible Team')
    source = fields.Selection([('internal', 'Internal'), ('customer', 'Customer'), ('supplier', 'Supplier'), ('faa', 'FAA'), ('external', "External Auditor")], string='Source of Issue', help="This is source of the CAR.", default="internal")
    partner_id = fields.Many2one('res.partner', string='Customer/Supplier', help="The related customer or supplier.")


    def create_car(self):
        vals = {
            'analytic_distribution': self.analytic_distribution,
            'champion_id': self.champion_id.id,
            'description': self.description,
            'ncr_report_id': self.ncr_report_id.id if self.ncr_report_id else False,
            'responsible_department_id': self.responsible_department_id.id,
            'subject': self.subject,
            'responsible_team_ids': self.responsible_team_ids.ids,
            'source': self.source,
            'partner_id': self.partner_id.id if self.partner_id else False

        }
                
        res = self.env['quality.car.report'].create(vals)
        
        return {
            'res_model': 'quality.car.report',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_id': res.id,
            'target': 'self',
        }
