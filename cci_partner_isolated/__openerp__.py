# -*- encoding: utf-8 -*-
{
    'name': 'cci_partner_isolated',
    'category': 'Views Module',
    'author': 'CCI Liege Verviers Namur',
    # great number of 'depends modules' because this module redefines menus of these modules
    'depends': ['cci_partner_extend','cci_membership_extend','cci_newsletter','cci_mission','marketing','mrp','event','cci_event','cci_base_contact','sale_advertising',],
    'version': '1.0.0',
    'data':[
        'security/security.xml',
        'views/res_partner.xml',
        'views/menus.xml',
	],
    'demo': [],
    'auto_install': False,
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


