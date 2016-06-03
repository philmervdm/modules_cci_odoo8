# -*- encoding: utf-8 -*-
{
    'name': 'CCI Premium Proxy',
    'category': 'CCI',
    'init_xml':[],
    'author': 'Philmer - CCILVN',
    'depends': ['base','base_vat','cci_base_contact','cci_premium','cci_premium_data','cci_activity_sector'],
    'version': '1.0',
    'active': False,
    'demo': [],
    'data':[
        'security/security.xml',
        'security/ir.model.access.csv',
        'cci_premium_proxy_view.xml',
        'wizard/inject_premium_company_view.xml',
        'wizard/inject_premium_contact_view.xml',
        'wizard/view_companies.xml',
        'wizard/search_poss_contacts.xml'
	],
    'installable': True
}


