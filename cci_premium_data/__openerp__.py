# -*- encoding: utf-8 -*-
{
    'name': 'CCI Premium Data',
    'category': 'CCI',
    'init_xml':[],
    'author': 'Philmer - CCILVN',
    'depends': ['base',
                #'cci_base_contact','cci_last_module',
                'cci_premium'],
    'version': '1.0',
    'active': False,
    'demo': [],
    'data':[	
        'cci_premium_data_view.xml',
      'wizard/extract_premium_view.xml',
      'wizard/send_new_login_view.xml',
	],
    'installable': True
}


