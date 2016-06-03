# -*- encoding: utf-8 -*-
{
    'name': 'CCI Activity Sector',
    'category': 'CCI',
    'init_xml':[],
    'author': 'CCI Liege Verviers Namur',
    'depends': ['base','cci_partner'],
    'version': '1.0.0',
    'active': False,
    'demo': [],
    'data':[
        'security/ir.model.access.csv',
        'views/res_partner_activsector.xml',
        'views/res_partner.xml',
	],
    'installable': True,
    'application': False,
}


