# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
from openerp.exceptions import Warning

# form = """<?xml version="1.0"?>
# <form string="Options">
#     <field name="new_state" colspan="4"/>
# </form>"""


# msg_form = """<?xml version="1.0"?>
# <form string="Results">
#      <field name="msg" colspan="4" nolabel="1" width="600"/>
# </form>"""

class confirm_registration(models.TransientModel):
    
    _name = 'confirm.registration'

    new_state = fields.Selection([('draft','Draft'),('open','Open'),('done','Done'),('cancel','Cancel'),('same','Same as Proxy')], required=True, string='State')
    msg = fields.Text(string='Results', size=1500, readonly=True)

    @api.multi
    def try_to_confirm(self):
        # TODO : checker si partner_id, contact_id et event_id sont bien existants sinon message d'erreur
        # (mais comment puisque pas prévu de message en fin ... provoquer une erreur de wizard pour afficher un warning ?)
        proxy_obj = self.env['cci_event_proxy.registration']
        reg_obj = self.env['event.registration']
        event_obj = self.env['event.event']
        proxies = proxy_obj.browse(self.env.context.get('active_ids', False))
        good_ids = []
        goods = []
        errors = []
        to_checks = []
        for proxy in proxies:
            if proxy.active:
                corrected_ids = {}
                if not proxy.event_id and proxy.site_id:
                    # try to find the event id from the site_id
                    event_ids = event_obj.search([('site_id','=',proxy.site_id)])
                    if event_ids:
                        corrected_ids['event_id'] = event_ids[0]
                if not proxy.partner_id and (proxy.vat or proxy.company_name):
                    partner_id = proxy_obj._search_partner_on_vat_or_name(proxy.vat,proxy.company_name)
                    if partner_id:
                        corrected_ids['partner_id'] = partner_id
                if (proxy.partner_id or corrected_ids.has_key('partner_id')) and not proxy.contact_id and proxy.last_name:
                    contact_id = proxy_obj._search_contact((proxy.partner_id and proxy.partner_id.id or corrected_ids['partner_id']),proxy.last_name,proxy.first_name,proxy.login,proxy.motpasse)
                    if contact_id:
                        corrected_ids['contact_id'] = contact_id
                if corrected_ids:
                    proxy.write(corrected_ids)
                if proxy.event_id:
                    final_event_id = proxy.event_id.id
                else:
                    if corrected_ids.has_key('event_id'):
                        final_event_id = corrected_ids['event_id']
                    else:
                        final_event_id = False
                if proxy.partner_id:
                    final_partner_id = proxy.partner_id.id
                else:
                    if corrected_ids.has_key('partner_id'):
                        final_partner_id = corrected_ids['partner_id']
                    else:
                        final_partner_id = False
                if proxy.contact_id:
                    final_contact_id = proxy.contact_id.id
                else:
                    if corrected_ids.has_key('contact_id'):
                        final_contact_id = corrected_ids['contact_id']
                    else:
                        final_contact_id = False
                if final_event_id and final_partner_id and final_contact_id:
                    event = event_obj.browse(final_event_id)
                    if event.state in ('draft','fixed','open','confirm'):
                        # search if this contact_id is already registered to this event
                        reg_ids = reg_obj.search([('event_id','=',final_event_id),('partner_id','=',final_partner_id)])#,('contact_id','=',final_contact_id)])
                        if not reg_ids:
                            final_state = ((self.new_state == 'same') and proxy.state or self.new_state)
                            new_data = {'name':'Mobile registration: %s %s' % (proxy.last_name or '',proxy.first_name or ''),
                                        'event_id':final_event_id,
                                        'partner_id':final_partner_id,
                                        'partner_invoice_id':final_partner_id,
                                        'contact_id':final_contact_id,
                                        'state':final_state,
#                                         'invoice_label':event.product_id and event.product_id.name or '',
                                        'email_from':proxy.email or '',
                                        'comments':proxy.comments,
                                        'unit_price':proxy.price_wo_vat,
                                       }
                            new_reg_id = reg_obj.create(new_data)
                            again_data = {'email_from':proxy.email}
                            res = reg_obj.onchange_event2(final_event_id,final_partner_id)['value']
                            again_data['invoice_label'] = res['invoice_label']
                            res = reg_obj.onchange_partner_id2(final_partner_id,final_event_id)['value']
                            again_data['badge_partner'] = res['badge_partner']
                            # reg_obj.onchange_partner_invoice_id2(cr,uid,[new_reg_id],final_partner_id,final_event_id,final_partner_id,final_contact_id)
                            res = reg_obj.onchange_contact_id2(final_contact_id,final_event_id,final_partner_id,final_partner_id)['value']
                            again_data['badge_title'] = res['badge_title']
                            again_data['badge_name'] = res['badge_name']
                            again_data['unit_price'] = res['unit_price']
                            again_data['name'] = res['name']
                            reg_obj.write([new_reg_id],again_data)
                            if final_state == 'open':
                                new_reg_id.mail_user()
                            good_ids.append(new_reg_id.id)
                            proxy.write({'active':False,'registration_id':new_reg_id.id})
                            if again_data['unit_price'] == new_data['unit_price']:
                                goods.append(u'Inscription \'%s\' à \'%s\' ajoutée' % (proxy.last_name,event.name))
                            else:
                                to_checks.append(u'Inscription \'%s\' à \'%s\' ajoutée mais prix à vérifier' % (proxy.last_name,event.name))
                        else:
                            errors.append(u'Inscription de \'%s\' rejetée parce que cette personne est déjà inscrite à cet événement' % proxy.last_name )
                    else:
                        errors.append(u'Inscription de \'%s\' rejetée parce que : l\'événement n\'est plus actif' % proxy.last_name )
                else:
                    error = ''
                    if not final_event_id:
                        error = u"L'événement n'est pas reconnu"
                    if not final_partner_id:
                        if error:
                            error += u", le partenaire n'a pas été retrouvé"
                        else:
                            error = u"Le partenaire n'a pas été retrouvé"
                    if not final_contact_id:
                        if error:
                            error += u", la personne de contact n'a pas été retrouvée"
                        else:
                            error = u"La personne de contact n'a pas été retrouvée"
                    errors.append(u'Inscription de \'%s\' rejetée parce que : %s' % (proxy.last_name,error) )
            else:
                 errors.append(u'Inscription de \'%s\' rejetée parce que : %s' % (proxy.last_name,u'Inscription déjà versée') )
            # TODO : si status # draft, vérifier si les envois de mails de confirmation 1 et 2 se passent bien ou s'il faut actionner les chgs de status un par un
        res_message = u'Erreurs :\n%s\nA vérifier au niveau prix :\n%s\nRésultats OK :\n%s' % ('\n'.join(errors),'\n'.join(to_checks),'\n'.join(goods))
        view = self.env.ref('cci_event_proxy.view_confirm_registration_msg')
        ctx = self.env.context.copy()
        ctx.update({'msg': res_message})
        return {
            'name': _('Result'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'confirm.registration.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }
           
           
class confirm_registration_msg(models.TransientModel):
    
    _name = 'confirm.registration.msg'
    
    msg = fields.Text(string='Results', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(confirm_registration_msg, self).default_get(fields)
            
        if 'msg' in self.env.context:
            res.update({'msg': self.env.context['msg']})
        return res

# confirm_registration("confirm_registration")

