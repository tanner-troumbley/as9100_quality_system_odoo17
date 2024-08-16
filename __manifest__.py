# -*- coding: utf-8 -*-
{
    'name': "AS9100 Quality Systems",

    'summary': """
       Changes to Quality app to fulfill AS9100 requirements.""",

    'description': """
        This is an Odoo 17 customization I created for Electric Power Systems. I have made the necessary changes
        to be able to post this code in my personal repo.
        
        It is an overhaul of the quality system in Odoo 17 Enterprise to allow Non-conformance Reports and Correct Action reports
        as defined by Electric Power System Logan, UT and AS9100.
        
        It also allows employees that only need to access to AS9100_quality aspect to have an Odoo portal account to help save costs.
    """,

    'author': "Tanner Troumbley",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/17.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Administration',
    'version': '17.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['quality_mrp', 'quality_mrp_workorder', 'viewer_groups', 'analytic', 'portal', 'mrp_subcontracting'],
    'auto_install': True,

    'data': [
        'data/mail_template_data.xml',
        'data/quality_department.xml',
        'data/schedule_actions.xml',
        'data/sequences.xml',
        'wizard/quality_car_report_wizard.xml',
        'reports/quality_car_report_reports.xml',
        'reports/quality_ncr_action_reports.xml',
        'reports/quality_ncr_report_reports.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/mrp_production.xml',
        'views/mrp_workorder.xml',
        'views/quality_audit.xml',
        'views/quality_car_views.xml',
        'views/quality_ncr_action_views.xml',
        'views/quality_ncr_report_views.xml',
        'views/quality_views.xml',
        'views/res_partner.xml',
        'views/stock_lot.xml',
        'views/stock_picking_views.xml',
        'views/portal_templates.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'AS9100_quality/static/src/fields/state_selection/*',
            'AS9100_quality/static/src/components/*',
        ],
        'web.assets_frontend': [
            'AS9100_quality/static/src/portal/**/*',
        ]
    }
}
