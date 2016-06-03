# -*- coding: utf-8 -*-
{
    'name': 'Zip code management',
    'summary':'Change the way the zip codes are handled :\nwith this module, tou define all possible zip codes and just link them to res.partner.\nEach zip code manage also it''s own country.',
    'version':'1.0.0',
    'author':'CCI Liege Verviers Namur',
    'category':'Customer Relationship Management',
    'depends': ['base',],
    'data': ['views/res_partner_zip.xml',
             'views/res_partner_zip_group.xml',
             'views/res_partner_zip_group_type.xml',
            ]
}
