# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 CCI Connect ASBL. (http://www.cciconnect.be) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from openerp import models, fields, api , tools , _
import datetime
import string
from operator import itemgetter

class res_partner_contact(models.Model):
    
    _inherit = "res.partner"
    _description = "res.partner.contact"
    
    @api.depends('premium_begin','premium_end','premium_special')
    def _is_premium(self):
        for contact in self:
            if contact.premium_special == 'yes':
                contact.is_premium = 'OUI'
            elif contact.premium_special == 'no':
                contact.is_premium = ''
            else:
                contact.is_premium = ( contact.premium_begin and not contact.premium_end ) and 'OUI' or ''
    
    def _search_premium(self,operator, operand):
        if operand:
            return []
        if operand == 'OUI':
            self.env.cr.execute("""SELECT id FROM res_partner WHERE (( premium_begin IS NOT NULL AND premium_end IS NULL) OR premium_special = 'yes' ) AND NOT premium_special = 'no'""")
            res = self.env.cr.fetchall()
        else:
            self.env.cr.execute("""SELECT id FROM res_partner WHERE (premium_begin IS NULL OR premium_end IS NOT NULL OR premium_special = 'no') AND NOT premium_special = 'yes'""")
            res = self.env.cr.fetchall()
        if not len(res):
            return [('id','=','0')]
        return [('id','in',map(itemgetter(0), res))]
    
    premium_begin = fields.Date('Begin as Premium',help="Date of beginning as premium member")
    premium_end = fields.Date('End as Premium',help="Date of end as premium member")
    is_premium = fields.Char(compute='_is_premium', search='_search_premium', size=3,string='Premium')
    premium_special = fields.Selection([('yes','Always Yes'),('normal','Normal'),('no','Currently No')], default='normal',string='Special Premium')

# class res_partner_job(models.Model):
#     _inherit = "res.partner"
#     _description = "res.partner.job"
#     
#     is_premium = fields.Char(related = 'contact_id.is_premium', size=3,string='Premium',store=False)

class res_partner(models.Model):
    _inherit = "res.partner"
    _description = "res.partner"
    
    count_premium = fields.Char('Count Premium',size=7)
    
    @api.model
    def count_premium(self,max_changed=2000):
#         cronline_id = self.pool.get('cci_logs.cron_line')._start(cr,uid,'CountPremium')
        final_result = True
        errors = []
        # Before checking the count of premiums for partners, checks for validity of premium contact : today, we keep only premium linked to a at least one partner in 5... zip code non-members
        contact_obj = self.env['res.partner']
        contact_ids = contact_obj.search(['|',('premium_begin','>','2000-01-01'),('premium_special','=','no')])
        losts = []
        recups = []
        if contact_ids:
            contacts = contact_ids #contact_obj.browse(cr,uid,contact_ids)
            for contact in contacts:
                # calculate the good state
                if contact.premium_special == 'yes':
                    new_special = 'yes'
                else:
                    new_special = 'no'
                    if contact.other_contact_ids:
                        for job in contact.other_contact_ids:
                            if job.address_id and job.address_id.parent_id and job.address_id.zip_id:
                                if job.address_id.zip_id.name[0:1] == '5' and ( job.address_id.parent_id.membership_state not in ['free','invoiced','paid'] ) and job.address_id.partner_id.state_id.id == 1:
                                    new_special = 'normal'
                
                if new_special != contact.premium_special:
                    # modify the current state and save it to send as email at the end of the control
                    contact.write({'premium_special':new_special})
                    if new_special == 'no':
                        losts.append([str(contact.id),contact.name,contact.first_name or ''])
                    else:
                        recups.append([str(contact.id),contact.name,contact.first_name or ''])
            if losts or recups:
                # send mail to premium supervisors
#                 parameter_obj = self.pool.get('cci_parameters.cci_value')
                parameter_obj = self.env['ir.config_parameter']
                param_values = parameter_obj.search([('key','=','SupervisorsPremiumEmail')])[0].value
                
                if param_values:
                    email_text = u"""<p>Certains premiums ont été désactivés ou certains ont été réactivés. En voici la liste :</p>
                                     <p>Désactivés :<br/><ul><li>
                                     %s
                                     </li></ul></p>
                                     <p>Réactivés :<br/><ul><li>
                                     %s
                                     </li></ul></p>
                                  """ % (losts and '</li><li>'.join(x[1]+' '+x[2]+' ['+x[0]+']' for x in losts) or '--Aucun--',
                                         recups and '</li><li>'.join(x[1]+' '+x[2]+' ['+x[0]+']' for x in recups) or '--Aucun--')
                    tools.email_send('noreply@ccilvn.be', param_values, u'Changement dans les Premiums', email_text, subtype='html')
#         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'\nChanged Contacts :\n\nPremium Losts : \n- %s\n\nRecovered Premium : \n- %s' % ('\n- '.join(x[1]+' '+x[2]+' ['+x[0]+']' for x in losts),
#                                                                                                                                                              '\n- '.join(x[1]+' '+x[2]+' ['+x[0]+']' for x in recups)) )
        
        # For each of current premium members, we check if he has a free cci mag subscription and a free revue de presse subscription
        # TODO : this part of the medthod introduce a dependancy problem : this part use 'premium_subscription' object and the 'premium_subscription'
        # module depends of the 'premium' module. Be better to regroup the two modules into one or to split this part of the wizard into 
        # a separate wizard
        today = datetime.datetime.today().strftime('%Y-%m-%d')
#         contact_obj = self.pool.get('res.partner.contact')
        contact_ids = contact_obj.search([('is_premium','=','OUI')])
        if contact_ids:
            contacts = contact_ids #contact_obj.browse(cr,uid,contact_ids)
            obj_sub = self.env['premium_subscription']
            obj_product = self.env['product.product']
            obj_sub_type = self.env['premium_subscription.type']
            for contact in contacts:
                already_mag = False
                already_rdp = False
                if contact.subscription_ids:
                    for subscription in contact.subscription_ids:
                        if subscription.type_id.code == 'CCIMAG':
                            already_mag = True
                        elif subscription.type_id.code == 'RDP':
                            already_rdp = True
                if not already_mag:
                    # free subscription for two cci mag issues
                    new_id_sub = False
                    type_ids = obj_sub_type.search([('code','=','CCIMAG')])
                    if type_ids:
                        data_sub = {}
                        data_sub['name'] = u"Abonnement gratuit à deux parutions"
                        data_sub['date'] = datetime.datetime.today().strftime('%Y-%m-%d')
                        data_sub['begin'] = datetime.datetime.today().strftime('%Y-%m-%d')
                        end_date = datetime.datetime.today() + datetime.timedelta(days=62)
                        data_sub['end'] = end_date.strftime('%Y-%m-%d')
                        data_sub['contact_id'] = contact.id
                        data_sub['partner_id'] = False
                        data_sub['type_id'] = type_ids[0].id
                        data_sub['product_id'] = False
                        data_sub['price'] = 0.0
                        data_sub['source'] = 'Auto free'
                        data_sub['usages'] = 2
                        data_sub['left_usages'] = 2
                        data_sub['state'] = 'current'
                        data_sub['invoice_id'] = False
                        new_id_sub = obj_sub.create(data_sub)
#                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,u'\nNew free CCI Mag subscription for %s %s' % (contact.name,contact.first_name or '') )
                if not already_rdp:
                    # free subscription to 'Revue de Presse' for 14 days
                    new_id_sub = False
                    type_ids = obj_sub_type.search([('code','=','RDP')])
                    if type_ids:
                        data_sub = {}
                        data_sub['name'] = u"Abonnement gratuit à la Revue de Presse pour 14 jours"
                        data_sub['date'] = datetime.datetime.today().strftime('%Y-%m-%d')
                        data_sub['begin'] = datetime.datetime.today().strftime('%Y-%m-%d')
                        end_date = datetime.datetime.today() + datetime.timedelta(days=15)
                        data_sub['end'] = end_date.strftime('%Y-%m-%d')
                        data_sub['contact_id'] = contact.id
                        data_sub['partner_id'] = False
                        data_sub['type_id'] = type_ids[0].id
                        data_sub['product_id'] = False
                        data_sub['price'] = 0.0
                        data_sub['source'] = 'Auto free'
                        data_sub['usages'] = 0
                        data_sub['left_usages'] = 0
                        data_sub['state'] = 'current'
                        data_sub['invoice_id'] = False
                        new_id_sub = obj_sub.create(data_sub)
#                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,u'\nNew free RDP subscription for %s %s' % (contact.name,contact.first_name or '') )
           
        # We check for current 'répertoire électronique' subscriptions on non-premium contacts to transfert them to invoiced partner as partner_subscription
#         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,u'\nCheck if necessary to transfert premium subscriptions to company subscriptions' )
        contact_sub_type_obj = self.env['premium_subscription.type']
        contact_sub_type_ids = contact_sub_type_obj.search([('code','=','REPMEMBRE')])
        if contact_sub_type_ids:
            partner_sub_type_obj = self.env['partner_subscription.type']
            partner_sub_type_ids = partner_sub_type_obj.search([('code','=','SOCREPELEC')])
            if partner_sub_type_ids:
                product_obj = self.env['product.product']
                product_ids = product_obj.search([('partner_subscription_type_id','=',partner_sub_type_ids[0].id)])
                if product_ids:
                    contact_sub_obj = self.env['premium_subscription']
                    contact_sub_ids = contact_sub_obj.search([('state','=','current'),('type_id','in',contact_sub_type_ids)])
                    if contact_sub_ids:
                        contact_subs = contact_sub_ids #contact_sub_obj.browse(cr,uid,contact_sub_ids)
                        for contact_sub in contact_subs:
                            if contact_sub.contact_id and contact_sub.contact_id.is_premium <> 'OUI':
                                # try to transfert to partner if possible (patrner_id or through invoice_id.partner_id
                                data = {}
                                data['name'] = contact_sub.name or ''
                                data['end'] = contact_sub.end
                                data['invoice_id'] = contact_sub.invoice_id and contact_sub.invoice_id.id or 0
                                if contact_sub.partner_id:
                                    data['partner_id'] = contact_sub.partner_id.id
                                elif contact_sub.invoice_id:
                                    data['partner_id'] = contact_sub.invoice_id.partner_id.id
                                data['type_id'] = partner_sub_type_ids[0]
                                data['product_id'] = product_ids[0]
                                data['price'] = contact_sub.price or 0.0
                                data['source'] = 'Transfert From Contact'
                                data['state'] = 'current'
                                partner_sub_obj = self.env['partner_subscription']
                                new_id = partner_sub_obj.create(data)
                                if new_id:
                                    contact_sub.button_close()
                                    contact_sub.write({'close_source':'Transfert'})
                    else:
                        pass
#                         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,u'\nNo contract to transfert.' )
                else:
                    errors.append('0')
#                     self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,u'\nNo product defined for partner subscriptions of type \'REPMEMBRE\'.' )
            else:
                errors.append('0')
#                 self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,u'\nNo type of partner subscriptions found with the code \'SOCREPELEC\'.' )
        else:
            errors.append('0')
#             self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,u'\nNo type of premium subscriptions found with the code \'REPMEMBRE\'.' )
        # Now we can recount the count_premium of each partner
        partner_obj = self.env['res.partner']
        partner_ids = partner_obj.search([])
        changed = 0
        checked = 0
        if partner_ids:
            index = 0
            part = 500
            while index < len(partner_ids) and ( changed < max_changed ):
                partners  = partner_ids[index:index+part]
                for partner in partners:
                    max_premium = 0
                    nbr_premium = 0
                    for addr in partner.child_ids:
                        for job in addr.other_contact_ids:
                            max_premium += 1
                            if addr.is_premium:
                                nbr_premium += 1
                    new_value = '%i/%i' % (nbr_premium,max_premium)
                    checked += 1
                    if partner.count_premium != new_value:
                        try:
                            partner.write({'count_premium':new_value})
                            changed += 1
                        except Exception:
                            errors.append(str(partner.id))
                index += part
#         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'\n\nChecked : %d' % checked )
#         self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'\nChanged : %d' % changed )
        if errors:
#             self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'\nPartners not changed - errors : [%s]' % (','.join(errors)) )
            final_result = False
#         self.pool.get('cci_logs.cron_line')._stop(cr,uid,cronline_id,final_result,'\n---end---')
        return True
