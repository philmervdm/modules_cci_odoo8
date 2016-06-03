# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################
# 2012-02-16 : some 'job.' -> 'sel_job.'
# 2012-09-11 : select only open history
import datetime
from openerp import api, fields, models, _


class get_cci_todos(models.TransientModel):
    _name = 'get.cci.todos'
    
    @api.model
    def get_phone_country_prefix(self):
        result = []
        obj_country = self.env['cci.country']
        country_ids = obj_country.search([('phoneprefix','!=',False),('phoneprefix','!=',0)])
        if country_ids:
            countries = country_ids.read(['phoneprefix'])
            result = [str(x['phoneprefix']) for x in countries]
        return result
    
    @api.model
    def convert_phone(self,string,PHONE_COUNTRY_PREFIX):
        def only_digits(string):
            cleaned = ''
            for carac in string:
                if carac in '0123456789':
                    cleaned += carac
            return cleaned
        result = ''
        string = string and only_digits(string) or ''
        if len(string) > 0:
            if len(string) == 9:
                if string[0:2] in ['02','03','04','09']:
                    result = string[0:2] + "/" + string[2:5] + "." + string[5:7] + "." + string[7:]
                else:
                    result = string[0:3] + "/" + string[3:5] + "." + string[5:7] + "." + string[7:]
            elif len(string) == 10:
                result = string[0:4] + "/" + string[4:6] + "." + string[6:8] + "." + string[8:]
            else:
                # international number
                #print string
                if string[0:2] == '00':
                    # search after a country with this prefix
                    prefix = string[2:4]
                    if prefix not in PHONE_COUNTRY_PREFIX:
                        prefix = string[2:5]
                        if prefix not in PHONE_COUNTRY_PREFIX:
                            prefix = string[2:6]
                            if prefix not in PHONE_COUNTRY_PREFIX:
                                prefix = ''
                    if prefix:
                        result = '+' + string[2:2+len(prefix)] + ' ' + string[2+len(prefix):4+len(prefix)]
                        rest = string[4+len(prefix):]
                        while len(rest) > 3:
                            result += '.' + rest[0:2]
                            rest = rest[2:]
                        result += '.' + rest
                    else:
                        result = 'International:'+string
        return result

    @api.multi
    def open_window_results(self):
        # todo list for current uid
        current_user_id = self.env.uid
        # delete all old values
        selection = "DELETE FROM crm_cci_todo WHERE cci_contact_follow = %s" % current_user_id
        self.env.cr.execute( selection )
        selection = '' # unusefull just for the case of
        # prepare the inserting of new data
        todo_obj = self.env['crm_cci.todo']
        minter_obj = self.env['res.partner.interest']
        phist_obj = self.env['res.partner.history']
        PREFIXES = self.get_phone_country_prefix()
        # get this list of interests still active and linked to the current user
        minter_ids = minter_obj.search([('cci_contact_follow','=',current_user_id)])
        new_ids = []
        if minter_ids:
            # get all data for interests concerned
#             interests = minter_obj.browse(minter_ids)
            for inter in minter_ids:
                if inter.contact:
                    pphone = self.convert_phone( inter.contact.phone, PREFIXES )
                    pemail = inter.contact.email or inter.contact.contact_id.email or ''
                    if inter.contact.address_id:
                        cphone = self.convert_phone( inter.contact.address_id.phone, PREFIXES )
                        cemail = inter.contact.address_id.email or ''
                    else:
                        cphone = ''
                        cemail = ''
                    if inter.contact.contact_id:
                        pmobile = self.convert_phone(inter.contact.contact_id.mobile, PREFIXES )
                    else:
                        pmobile = ''
                else:
                    cphone = ''
                    pphone = ''
                    cemail = ''
                    pemail = ''
                    pmobile = ''
                new_value = {'model':u"Marque d'intérêt",
                             'res_id':inter.id,
                             'partner': inter.partner.id,
                             'date': inter.date,
                             'product': inter.product and inter.product.id or 0,
                             'cci_contact': inter.cci_contact and inter.cci_contact.id or 0,
                             'contact': inter.contact and inter.contact.id or 0,
                             'category': inter.category and inter.category.id or 0,
                             'turnover_hoped': inter.turnover_hoped,
                             'next_action': inter.next_action, 
                             'cci_contact_follow': inter.cci_contact_follow and inter.cci_contact_follow.id or 0,
                             'description': inter.description,
                             'year': inter.year,
                             'action': '/',
                             'state': 'open',
                             'company_phone': cphone,
                             'prof_phone': pphone,
                             'mobile': pmobile,
                             'company_email': cemail,
                             'prof_email': pemail,
                             'positive': inter.positive,
                            }
                new_id = todo_obj.create(new_value)
                if new_id:
                    new_ids.append(new_id.id)
        phist_ids = phist_obj.search([('cci_contact_follow','=',current_user_id),('next_action','>','1980-01-01'),('state','=','open')])
        if phist_ids:
            # get all data for histories concerned
            histories = phist_ids.browse()
            for inter in histories:
                if inter.contact:
                    pphone = self.convert_phone( inter.contact.phone, PREFIXES )
                    pemail = inter.contact.email or inter.contact.contact_id.email or ''
                    if inter.contact.address_id:
                        cphone = self.convert_phone( inter.contact.address_id.phone, PREFIXES )
                        cemail = inter.contact.address_id.email or ''
                    else:
                        cphone = ''
                        cemail = ''
                    if inter.contact.contact_id:
                        pmobile = self.convert_phone(inter.contact.contact_id.mobile, PREFIXES )
                    else:
                        pmobile = ''
                else:
                    cphone = ''
                    pphone = ''
                    cemail = ''
                    pemail = ''
                    pmobile = ''
                new_value = {'model':u'Historique',
                             'res_id':inter.id,
                             'partner': inter.partner.id,
                             'date': inter.date,
                             'product': inter.product and inter.product.id or 0,
                             'cci_contact': inter.cci_contact and inter.cci_contact.id or 0,
                             'contact': inter.contact and inter.contact.id or 0,
                             'category': inter.category and inter.category.id or 0,
                             'turnover_hoped': 0.0,
                             'next_action': inter.next_action, 
                             'cci_contact_follow': inter.cci_contact_follow and inter.cci_contact_follow.id or 0,
                             'description': inter.description,
                             'year': 0,
                             'action': inter.action,
                             'state': inter.state,
                             'company_phone': cphone,
                             'prof_phone': pphone,
                             'mobile': pmobile,
                             'company_email': cemail,
                             'prof_email': pemail,
                             'positive': False,
                            }
                new_id = todo_obj.create(new_value)
                if new_id:
                    new_ids.append(new_id.id)
        result = {
            'name': _('ToDo'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'crm_cci.todo',
            'domain': [('id','in',new_ids)],
            'context': {},
            'type': 'ir.actions.act_window',
            'limit':300,
        }
        #    'domain': "[('cci_contact_follow','=',uid)]",
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

