# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _

class cci_event_proxy_registration(models.Model):
    _name = 'cci_event_proxy.registration'
    _description='cci_event_proxy_registration'

    event_id = fields.Many2one('event.event','Event')
    site_id = fields.Integer('Event ID on WebSite')
    event_name = fields.Char('Event Name',size=120)
    first_name = fields.Char('First Name',size=120)
    last_name = fields.Char('Last Name',size=120)
    company_name = fields.Char('Company Name',size=120)
    vat = fields.Char('VAT/Company ID',size=50)
    comments = fields.Text("User Comments")
    price_wo_vat = fields.Float("Price wo VAT",digits=(15,2))
    price_w_vat = fields.Float("Price with VAT",digits=(15,2))
    state = fields.Selection([('draft','Draft'),('confirm','Confirmed'),('done','Done'),('cancel','Canceled')], 'Status', default='draft')
    email = fields.Char('Email',size=200)
    street = fields.Char('Street',size=120)
    zip_code = fields.Char('Zip Code',size=10)
    zip_city = fields.Char('Zip City',size=60)
    phone = fields.Char('Phone',size=40)
    courtesy = fields.Char('Courtesy',size=30)
    title = fields.Char('Title',size=240)
    mobile = fields.Char('Mobile',size=60)
    login = fields.Char('Login Premium',size=100)
    motpasse = fields.Char('Password Premium',size=100)
    partner_id = fields.Many2one('res.partner','Linked Partner')
    contact_id = fields.Many2one('res.partner','Linked Contact')
    active = fields.Boolean('Active', default=True)
    registration_id = fields.Many2one('event.registration','Registration')
    
    def _search_partner_on_vat_or_name(self, vat, company_name):
        partner_id = False
        correct_vat = False
        if vat:
            vat = vat.replace('.','').replace('-','').replace(' ','').replace('/','').upper()
            if len(vat) > 2:
                if vat[0:2] == 'BE':
                    if len(vat) == 12:
                        # on a un numéro bien formaté
                        correct_vat = vat
                    else:
                        if len(vat) == 11:
                            # on suppose que c'est l'erreur classique : le user a indiqué BE et le numéro de TVA à 9 chiffres
                            correct_vat = vat[0:2] + '0' + vat[2:]
                        else:
                            # on est en terrain inconnu => on n'a pas de vat valable pour faire une recherche
                            correct_vat = False
                else:
                    # on vérifie si on a 9 chiffres et seulement cela
                    if len(vat) == 9 and vat.isdigit():
                        correct_vat = 'BE0' + vat
                    elif len(vat) == 10 and vat.isdigit():
                        correct_vat = 'BE' + vat
                    elif vat[0:2] in ['FR','NL','LU']:
                        # on va essayer comme cela
                        correct_vat = vat
                    else:
                        correct_vat = False
        if correct_vat:
            partner_ids = self.env['res.partner'].search([('vat','=',correct_vat)])
            if partner_ids and len(partner_ids) == 1:
                partner_id = partner_ids[0].id
        if not partner_id:
            # The search on vat is unsuccessfull, we'll try on name
            partner_ids = self.env['res.partner'].search([('name','=',company_name.strip().upper())])
            if partner_ids and len(partner_ids) == 1:
                partner_id = partner_ids[0].id
        return partner_id

    def _search_contact(self, partner_id, last_name, first_name, login, motpasse):
        contact_id = False
        if login and motpasse:
            contact_ids = self.env['res.partner'].search([('premium_login','=',login),('premium_mp','=',motpasse)])
            if contact_ids and len(contact_ids) == 1:
                contact_id = contact_ids[0].id
        if not contact_id and last_name:
            partner = self.env['res.partner'].browse(partner_id)
            last_name = last_name.upper()
            first_name = (first_name or '').upper()
            if first_name:
                # if first_name, we search on exact comparison on name and first_name
                if partner.child_ids:
                        for job in partner.child_ids:
                            if job.contact_id and job.contact_id.name.strip().upper() == last_name.strip().upper() and job.contact_id.first_name.strip().upper() == first_name.strip().upper():
                                contact_id = job.contact_id.id
                                break
                            if contact_id:
                                break
            else:
                # no first name => we search if we have one and only one contact with given name
                contact_ids = []
                if partner.child_ids:
                    for job in partner.child_ids:
                        if job.contact_id and job.contact_id.name.strip().upper() == last_name.strip().upper():
                            contact_ids.append( job.contact_id.id )
                if contact_ids and len(contact_ids) == 1:
                    contact_id = contact_ids[0]
        return contact_id

    @api.model
    def create(self, vals):
        if vals['site_id'] and not vals.get('event_name',False):
            event_ids = self.env['event.event'].search([('site_id','=',vals['site_id'])])
            if event_ids:
                vals['event_name'] = event_ids[0].name
                print"\n\n\nvaalss.",vals
        return super(cci_event_proxy_registration,self).create(vals)

    @api.multi
    def write(self, vals):
        # TODO actionner les recherches si les valeurs ont changés et que partner_id et/ou contact_id sont vides
        #current_value = self.pool.get('cci_event_proxy.registration').browse(cr,uid,ids)[0]
        #print 'partner_id'
        #print current_value.partner_id.id
        #print "vals['partner_id']"
        #if vals.get('partner_id',False):
        #    print vals['partner_id']
        #else:
        #    print 'no value'
        #print "write vals"
        #print vals
        #print 'get'
        #print vals.get('partner_id',False)
        #if current_value.partner_id and current_value.partner_id.id > 0 and not vals.get('partner_id',False):
        #    print u'Manually deleted by user => do nothing'
        #elif vals.get('partner_id',False) and current_value.partner_id and current_value.partner_id.id > 0:
        #    print u"un partenaire a été encodé manuellement => on garde cette valeur"
        #elif not vals.get('partner_id',False) and not current_value.partner_id:
        #    print u"il n'y avait pas de valeur et il n'y en a toujours pas => on recherche"
        #    partner_id = self._search_partner_on_vat_or_name(cr,uid,vals['vat'],vals['company_name'],context)
        #    if partner_id:
        #        pass
        return super(cci_event_proxy_registration, self).write(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

