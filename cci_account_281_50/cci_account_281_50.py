#!/usr/bin/python
#-*- encoding: utf8 -*-
from openerp import models, fields, api , _

class account_partner281_50(models.Model):
    _name = 'account.partner281_50'

    @api.depends('calc_sum_a','manual_sum_b','calc_sum_b','calc_sum_c','calc_sum_d')
    def _sum_e(self):
        for record in self:
            record.calc_sum_e = ( ( record.calc_sum_a or 0.0 ) + \
                                  ( record.manual_sum_b or record.calc_sum_b or 0.0 ) + \
                                  ( record.calc_sum_c or 0.0 ) + \
                                  ( record.calc_sum_d or 0.0 ) )
    
    partner_id =  fields.Many2one('res.partner','Partner',required=True)
    final_sequence =  fields.Integer('Final Sequence')
    year = fields.Char('Year',size=4)
    name = fields.Char('Name',size=120)
    street1 = fields.Char('Street1',size=120)
    street2 = fields.Char('Street2',size=120)
    zip_code = fields.Char('Zip Code',size=4)
    city = fields.Char('City',size=120)
    company_number = fields.Char('Company Number',size=20)
    national_number = fields.Char('Personal National Number',size=20)
    profession = fields.Char('Profession',size=50)
    calc_sum_a = fields.Float('Sum A',digits=(15,2))
    calc_sum_b = fields.Float('Sum B',digits=(15,2))
    manual_sum_b = fields.Float('Forced Sum B',digits=(15,2))
    calc_sum_c = fields.Float('Sum C',digits=(15,2))
    calc_sum_d = fields.Float('Sum D',digits=(15,2))
    calc_sum_e = fields.Float(compute='_sum_e', string='Sum E', digits=(15,2))
    calc_sum_fa = fields.Float('Sum Fa',digits=(15,2))
    calc_sum_fb = fields.Float('Sum Fb',digits=(15,2))
    calc_sum_g = fields.Float('Sum G',digits=(15,2))
    final_output = fields.Datetime('Final Output')
