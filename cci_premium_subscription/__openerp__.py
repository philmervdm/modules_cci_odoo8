# -*- encoding: utf-8 -*-
{
    'name': 'CCI Premium Subscriptions',
    'category': 'CCI',
    'init_xml':[],
    'author': 'Philmer - CCILVN',
    'depends': ['base','cci_premium','sale_advertising'],#'cci_email_template'],
    'version': '1.1',
    'active': False,
    'demo': [],
    'data':[	
        'security/security.xml',
        'security/ir.model.access.csv',
        'cci_premium_subscription_view.xml',
        'wizard/create_sub_rdp.xml',
        'wizard/create_sub_mag.xml',
        'wizard/create_sub_full_page.xml',
        'wizard/send_memberdirectory_access.xml',
	],
    'installable': True
}


