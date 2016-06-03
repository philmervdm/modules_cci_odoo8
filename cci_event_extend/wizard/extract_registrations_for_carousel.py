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
# Version 1.0 Philmer
import time
import datetime
from openerp import tools
import base64
import dbf
from openerp import models, fields, api, _

class cci_extract_carousel(models.TransientModel):
    _name = 'cci.extract.carousel'
    
    choice = fields.Selection(selection=[('all', 'Toutes les inscriptions'), ('selected', 'Seulement les actives')], string='Selection', required=True, default='all')
    category_id = fields.Many2one('res.partner.category',  string='Activity Sectors Root', required=True)

    @api.multi
    def get_file(self):
        # we search for the ID of the CCI to correctly identify participers of this special partner
        cci_partner_id = 0
        obj_company = self.env['res.company']
        companies = obj_company.search([('parent_id', '=', False)], limit=1)
        if companies:
            company = companies.read(['partner_id'])
            cci_partner_id = company[0]['partner_id'][0]

        obj_registration = self.env['event.registration']

        # extract all ids of activity sector categories and keep only what is between [] ('[303]') in name
        obj_categ = self.env['res.partner.category']
        old_len = 0
        categ_ids = [self.category_id.id]
        while len(categ_ids) > old_len:
            new_ids = categ_ids[old_len:]  # ids of categories added last time
            old_len = len(categ_ids)  # the new frontier ...
            news = obj_categ.browse(new_ids)
            new_categs = news.read(['child_ids'])
            for categ in new_categs:
                if categ['child_ids']:
                    categ_ids.extend(categ['child_ids'])
                    
        categs_ids = obj_categ.browse(categ_ids)
        categs = categs_ids.with_context({'lang':'fr_FR'}).read(['name'])
        dCategs = {}
        for categ in categs:
            formated_name = categ['name']
            posA = formated_name.rfind('[')
            posB = formated_name.rfind(']')
            if posA > 0 and posB > 0 and posA < posB:
                formated_name = formated_name[posA + 1:posB]
            dCategs[categ['id'] ] = formated_name

        # search the registrations linked to the selected events
        if self.choice == 'all':
            reg_ids = obj_registration.search([('event_id', 'in', self.env.context['active_ids'])])
        else:
            reg_ids = obj_registration.search([('event_id', 'in', self.env.context['active_ids']), ('state', 'in', ['open', 'done'])])
        if reg_ids:
            registrations = reg_ids
        else:
            registrations = []

        table = dbf.Table('carousel.dbf', field_specs='Civilite C(20); TradCiv1 C(25); TradCiv2 C(25); Nom C(25); Titre C(45); Societe C(45); Adresse C(45); Localite C(45); Tel C(30); Fax C(30); EMail C(50); Montant N(15,2); Paiement C(9); Facture C(12); MbrePaye L; MbreClie L; Groupe C(45); Signet C(5); Logo C(250); Photo C(250); RefEntity C(8); RefContact C(8); RefClient C(8); Secteur C(5); Service1 I; Service2 I; Service3 I; CCI L; Present L; Inscrit L; WebURL C(100); ID I', dbf_type='vfp', codepage='cp850')
        table.open()
        for reg in registrations:
            # construction of the full name
            full_name = '' # reg.contact_id.name or 
#             if reg.contact_id.first_name:
#                 full_name = full_name + ' ' + reg.contact_id.first_name
            # research of the concerned job and address if this contact has multiple jobs or this partner has multiple address
            current_partner = False
            current_address = False
            current_job = False
            if reg.partner_id:
                current_partner = reg.partner_id
                if len(reg.partner_id.child_ids) == 1:
                    current_address = reg.partner_id.child_ids[0]
                    for job in current_address.other_contact_ids:
                        if job.contact_id.id == reg.contact_id.id:
                            current_job = job
                else:
                    if reg.partner_id.child_ids:
                        # some addresses to search for
                        for addr in reg.partner_id.child_ids:
                            for job in addr.other_contact_ids:
                                if job.contact_id.id == reg.contact_id.id:
                                    current_job = job
            # get the sector of activity
            sector = ''
            for activ in reg.partner_id.category_id:
                if dCategs.has_key(activ.id):
                    sector = dCategs[activ.id]
                    break
            table.append((reg.partner_id.title or 'Monsieur',
                           '',
                           '',
                           full_name[:25],
                           (current_job and current_job.function_label or '')[:45],
                           (current_partner and current_partner.name or '')[:45],
                           '',
                           '',
                           '',
                           '',
                           '',
                           0.0,
                           '',
                           '',
                           False,
                           False,
                           '',
                           '',
                           '',
                           '',
                           'P' + str(current_partner and current_partner.id or 0),
                           'C' + str(reg.contact_id.id),
                           'P' + str(current_partner and current_partner.id or 0),
                           sector[:5],
                           0,
                           0,
                           0,
                           current_partner.id == cci_partner_id,
                           False,
                           False,
                           '',
                           reg.id
                          ))
        table.close()
        result_file = open('carousel.dbf', 'rb').read()

        # give the result tos the user
        msg = 'Save the File with '".dbf"' extension.'
        carousel_dbf = base64.encodestring(result_file)
        
        ctx = self.env.context.copy()
        ctx.update({'msg': msg, 'carousel_dbf': carousel_dbf})
        
        resource = self.env.ref('cci_event_extend.cci_extract_carousel_msg_view')
        return {
            'name': 'Notification',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cci.extract.carousel.msg',
            'views': [(False, 'tree'), (resource.id, 'form')],
            'context': ctx,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

class cci_extract_carousel_msg(models.TransientModel):
    _name = 'cci.extract.carousel.msg'
    
    msg = fields.Text(string='File created', readonly=True)
    carousel_dbf = fields.Binary(string='Prepared file', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(cci_extract_carousel_msg, self).default_get(fiedls)
        if 'msg' in self.env.context:
            res.update({'msg': self.env.context['msg']})
        
        if 'carousel_dbf' in self.env.context:
            res.update({'carousel_dbf': self.env.context['carousel_dbf']})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
