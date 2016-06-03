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

import time
from openerp import tools
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class event_meeting_table(models.Model):
    _name = 'event.meeting.table'
    _description = 'event.meeting.table'
    
    partner_id1 = fields.Many2one('res.partner', string='First Partner', required=True)
    partner_id2 = fields.Many2one('res.partner', string='Second Partner', required=True)
    event_id = fields.Many2one('event.event', string='Related Event', required=True)
    contact_id1 = fields.Many2one('res.partner', string='First Contact', required=True)
    contact_id2 = fields.Many2one('res.partner', string='Second Contact', required=True)
    service = fields.Integer('Service', required=True)
    table = fields.Char('Table', size=10, required=True)

class event_check_type(models.Model):
    _name = 'event.check.type'
    _description = 'event.check.type'

    name = fields.Char('Name', size=20, required=True)

class event(models.Model):
    
    @api.multi
    def cci_event_fixed(self):
        self.write({'state':'fixed'})
        return True
    
    @api.multi
    def cci_event_open(self):
        self.write({'state':'open'})
        return True
    
    @api.multi
    def cci_event_confirm(self):
        for eve in self:
            if eve.mail_auto_confirm:
                # send reminder that will confirm the event for all the people that were already confirmed
                reg_ids = self.env['event.registration'].search([('event_id', '=', eve.id) ('state', 'not in', ['draft', 'cancel'])])
                if reg_ids:
                    reg_ids.mail_user_confirm()
        self.write({'state':'confirm'})
        return True
    
    @api.multi
    def cci_event_running(self):
        self.write({'state':'running'})
        return True
    
    @api.multi
    def cci_event_done(self):
        self.write({'state':'done'})
        return True
    
    @api.multi
    def cci_event_closed(self):
        self.write({'state': 'closed'})
        return True
    
    @api.multi
    def cci_event_cancel(self):
        self.write({'state':'cancel', })
        reg_ids = self.env['event.registration'].search([('event_id', 'in', self.ids)])
        reg_ids.cci_event_reg_cancel()
        return True
    
    @api.onchange('type')
    def onchange_check_type(self):
        if not self.type:
            return {}
        return {'value':{'check_type' : self.type.check_type.id}}
    
    @api.model
    def _group_names(self):
        self.env.cr.execute('''
        SELECT distinct name
        FROM event_group
        ''')
        res = self.env.cr.fetchall()
        temp = []
        for r in res:
            temp.append((r[0], r[0]))
        return temp

    _inherit = 'event.event'
    _description = 'event.event'
            
    state = fields.Selection([('draft', 'Draft'), ('fixed', 'Fixed'), ('open', 'Open'), ('confirm', 'Confirmed'), ('running', 'Running'), ('done', 'Done'), ('cancel', 'Canceled'), ('closed', 'Closed')], string='State', readonly=True, required=True)
    agreement_nbr = fields.Char('Agreement Nbr', size=16)
    note = fields.Text('Note')
    fse_code = fields.Char('FSE code', size=64)
    fse_hours = fields.Integer('FSE Hours')
    signet_type = fields.Selection(selection='_group_names', string='Signet Type')
    localisation = fields.Char('Localisation', size=20)
    check_type = fields.Many2one('event.check.type', string='Check Type')
    name_on_site = fields.Char('Name on Site', size=128)

class event_check(models.Model):
    _name = "event.check"
    _description = "event.check"
    
    @api.multi
    def cci_event_check_block(self):
        self.write({'state':'block'})
        return True
    
    @api.multi
    def cci_event_check_confirm(self):
        self.write({'state':'confirm'})
        return True
    
    @api.multi
    def cci_event_check_cancel(self):
        self.write({'state':'cancel'})
        return True

    name = fields.Char('Name', size=128, required=True, default='cheque')
    code = fields.Char('Code', size=64)
    reg_id = fields.Many2one('event.registration', string='Inscriptions', required=True)
    state = fields.Selection([('draft', 'Draft'), ('block', 'Blocked'), ('confirm', 'Confirm'), ('cancel', 'Cancel'), ('asked', 'Asked')], string='State', readonly=True, default='draft')
    unit_nbr = fields.Float(string='Value')
    type_id = fields.Many2one('event.check.type', string='Type')
    date_reception = fields.Date(string='Reception Date')
    date_limit = fields.Date(string='Limit Date')
    date_submission = fields.Date(string='Submission Date')
    
class event_type(models.Model):
    _inherit = 'event.type'
    _description = 'Event type'

    check_type = fields.Many2one('event.check.type', string='Default Check Type')

class event_group(models.Model):
    _name = 'event.group'
    _description = 'event.group'

    name = fields.Char(string='Group Name', size=20, required=True)
    bookmark_name = fields.Char(string='Value', size=128)
    picture = fields.Binary(string='Picture')
    type = fields.Selection([('image', 'Image'), ('text', 'Text')], string='Type', required=True, default='text')
    
    @api.multi
    def name_get(self):
        if not len(self.ids):
            return []
        result = []
        for line in self:
            if line.bookmark_name:
                result.append((line.id, (line.name + ' - ' + line.bookmark_name)))
            else:
                result.append((line.id, line.name))
        return result

class event_registration(models.Model):
    
    @api.model
    def create(self, vals):
#       Overwrite the name fields to set next sequence according to the sequence in the legalization type (type_id)
        if vals['name'] == 'Registration:' or vals['name'] == 'Registration':
            vals['name'] = False  # to be sure to have the contact name with 'Registration'
#         vals['badge_name'] = vals['badge_title'] = vals['badge_partner'] = False
#         if not vals['badge_name'] or not vals['name']:
#             newvals = self.onchange_contact_id(vals['contact_id'], vals['partner_id'])
#             if newvals['value'].has_key('badge_name'):
#                 vals.update({'badge_name':newvals['value']['badge_name']})
#             if newvals['value'].has_key('badge_title'):
#                 vals.update({'badge_title':newvals['value']['badge_title']})
#             if newvals['value'].has_key('name'):
#                 vals.update({'name':newvals['value']['name']})
#             if newvals['value'].has_key('email_from'):
#                 vals.update({'email_from':newvals['value']['email_from']})
        # check if there is a warning on the partner : in this case, add this warning to the comments field
        # to get it when the registration is created from Internet not manually
        if vals.get('partner_id'):
            data_partner = self.env['res.partner'].browse(vals['partner_id'])
            if data_partner.alert_events:
                if vals.has_key('comments') and vals['comments']:
                    vals['comments'] += "\n\nAvertissement : " +  (self.partner_id.alert_explanation if self.partner_id.alert_explanation else '')
                else:
                    vals['comments'] = "Avertissement : " + (self.partner_id.alert_explanation if self.partner_id.alert_explanation else '')
#         if not vals['badge_partner']:
#             newvals = self.onchange_partner_id(vals['partner_id'], vals['event_id'], False)
#             if newvals['value'].has_key('badge_partner'):
#                 vals.update({'badge_partner': newvals['value']['badge_partner']})
            # maybe unit_price and partner_invoice_id
        return super(event_registration, self).create(vals)
    
    @api.multi
    def cci_event_reg_draft(self):
        self.write({'state':'draft'})
#         self._history('Draft', history=True)
        return True
    
    @api.multi
    def cci_event_reg_open(self):
        self.write({'state':'open'})
        for registration in self:
#             if registration.event_id.mail_auto_confirm or registration.event_id.mail_auto_registr:
            registration.mail_user()
#         self._history('Open', history=True)
        return True
    
    @api.multi
    def cci_event_reg_done(self):
        self.write({'state':'done', })
#         self._history('Done', history=True)
        return True
    
    @api.multi
    def cci_event_reg_cancel(self):
        self.write({'state':'cancel', 'unit_price':0.0})
#         self._history('Cancel', history=True)
        return True
    
    @api.depends('check_ids')
    def cal_check_amount(self):
        res = {}
        for reg in self:
            total = 0
            for check in reg.check_ids:
                total = total + check.unit_nbr
            reg.check_amount = total
    
    @api.depends('check_ids')
    def get_nbr_checks(self):
        for reg in self:
            reg.nbr_event_check = len(reg.check_ids)
    
    @api.multi
    def _create_invoice_lines(self, vals):
        for reg in self:
            note = ''
            cci_special_reference = False
            if reg.check_mode:
                note = 'Check payment for a total of ' + str(reg.check_amount)
                cci_special_reference = "event.registration*" + str(reg.id)
                vals.update({
                    'note': note,
                    'cci_special_reference': cci_special_reference,
                })
        return self.env['account.invoice.line'].create(vals)

    # this method overwrites the parent method to make it more adapted to CCI events
#     @api.multi
#     def mail_user_confirm(self):
#         for reg_id in self:
#             src = reg_id.event_id.reply_to or False
#             # if not reg_id.email_from:
#             #    raise osv.except_osv(_('Warning!') _('You should specify Partner Email for registration "%s" !')%(reg_id.name,))
#             dest = []
#             if reg_id.email_from:
#                 dest += [reg_id.email_from]
#                 if reg_id.email_cc:
#                     dest += [reg_id.email_cc]
#             if dest and src:
#                 tools.email_send(src, dest,'Infos pratiques et liste des participants '+( reg_id.event_id.name_on_site and reg_id.event_id.name_on_site or reg_id.event_id.product_id.name ), reg_id.event_id.mail_confirm, tinycrm=str(reg_id.case_id.id), subtype='html')
  
#             if not src:
#                 raise Warning(_('Error!'), _('You must define a reply-to address in order to mail the participant. You can do this in the Mailing tab of your event. Note that this is also the place where you can configure your event to not send emails automaticly while registering'))
#         return False

    # this method overwrites the parent method to make it more adapted to CCI events
#     @api.multi
#     def mail_user(self):
#         for reg_id in self:
#             flag = ''
#             src = reg_id.event_id.reply_to or False
#             dest = []
#             if reg_id.email:
#                 dest += [reg_id.email]
#                 if reg_id.email_cc:
#                     dest += [reg_id.email_cc]
#             if reg_id.event_id.mail_auto_confirm or reg_id.event_id.mail_auto_registr:
                # if not reg_id.email_from:
                #    raise osv.except_osv(_('Warning!') _('You should specify Partner Email for registration "%s" !')%(reg_id.name,))
#                 if dest and src:
#                     if (reg_id.event_id.state in ['confirm', 'running']) and reg_id.event_id.mail_auto_confirm :
#                         flag = 't'
# #                         tools.email_send(src, dest, 'Infos pratiques et liste des participants ' + (reg_id.event_id.name_on_site and reg_id.event_id.name_on_site or reg_id.event_id.product_id.name), reg_id.event_id.mail_confirm, tinycrm=str(reg_id.case_id.id) subtype='html')
# #                     if reg_id.event_id.state in ['draft', 'fixed', 'open', 'confirm', 'running'] and reg_id.event_id.mail_auto_registr and not flag:
# #                         tools.email_send(src, dest, 'Confirmation inscription ' + (reg_id.event_id.name_on_site and reg_id.event_id.name_on_site or reg_id.event_id.product_id.name) reg_id.event_id.mail_registr, tinycrm=str(reg_id.case_id.id) subtype='html')
#                 if not src:
#                     raise Warning(_('Error!'), _('You must define a reply-to address in order to mail the participant. You can do this in the Mailing tab of your event. Note that this is also the place where you can configure your event to not send emails automaticly while registering'))
#         return False

    _inherit = 'event.registration'
    _description = "event.registration"
    
    contact_order_id = fields.Many2one('res.partner', string='Contact Order')
    grp_id = fields.Many2one('event.group', 'Event Group')
    cavalier = fields.Boolean('Cavalier', help="Check if we should print papers with participant name")
    payment_mode = fields.Many2one('payment.mode', 'Payment Mode')
    payment_linked = fields.Many2one('account.move.line', 'Linked Payment', domain=[('reconcile_id', '=', False), ('reconcile_partial_id', '=', False)])
    check_mode = fields.Boolean('Check Mode')
    check_ids = fields.One2many('event.check', 'reg_id', 'Check ids')
    payment_ids = fields.Many2many('account.move.line', 'move_line_registration', 'reg_id', 'move_line_id', string='Payment', readonly=True)
    training_authorization = fields.Char('Training Auth.', size=12, help='Formation Checks Authorization number', readonly=True)
    check_amount = fields.Float(compute='cal_check_amount', string='Check Amount')
    nbr_event_check = fields.Integer(compute='get_nbr_checks', string="Number of Checks", help="This field simply computes the number of event check records for this registration")
    comments = fields.Text(string='Comments')
    attendance = fields.Boolean(string='Attendance')
    ask_attest = fields.Boolean(string='Ask an attestation')
    name = fields.Char(default='Registration')
    
#     def onchange_contact_id(self, cr, uid, ids, contact, partner):
#         data = super(event_registration,self).onchange_contact_id(cr, uid, ids, contact, partner)
#         if not contact:
#             return data
#         contact = self.pool.get('res.partner.contact').browse(cr, uid, contact)
#         if contact.badge_name:
#             data['value']['badge_name'] = contact.badge_name
#         if contact.badge_title:
#             data['value']['badge_title'] = contact.badge_title
#         return data
     # overwrites complety the parent (event) method to accomodate to CCI way of life
    
#     @api.multi
#     def onchange_contact_id(self, contact, partner):
#         data = {}
#         if not contact:
#             return data
#         contact_id = self.env['res.partner'].browse(contact)
#         data['badge_name'] = contact_id.badge_name and contact_id.badge_name or (contact_id.name + ' ' + (contact_id.first_name  or '')).strip()
#         if partner:
#             partner_addresses = self.env['res.partner'].search([('partner_id', '=', partner)])
#             job_ids = self.env['res.partner'].search([('contact_id', '=', contact), ('address_id', 'in', partner_addresses.ids)], limit=1)
#             if job_ids:
#                 data['email_from'] = job_ids.email
#                 data['badge_title'] = contact_id.badge_title and contact_id.badge_title or job_ids.function_label
#         d = self.onchange_badge_name(data['badge_name'])
#         data.update(d['value'])
#         return {'value':data}
     
    @api.onchange('partner_id')
    def _onchange_partner(self):
        # raise an error if the partner cannot participate to event.
        warning = False
        if self.partner_id:
            if self.partner_id.alert_events:
                warning = {
                     'title': "Warning:",
                     'message': self.partner_id.alert_explanation or 'Partner is not valid'
                 }
        res = super(event_registration, self)._onchange_partner()
        return {'warning': warning}
     
#     @api.multi
#     def onchange_partner_invoice_id(self, event_id, partner_invoice_id):
#         data = {}
#         context = {}
#         data['training_authorization'] = data['unit_price'] = False
#         if partner_invoice_id:
#             data_partner = self.env['res.partner'].browse(partner_invoice_id)
#             data['training_authorization'] = data_partner.training_authorization
#         if not event_id:
#             return {'value':data}
#         data_event = self.env['event.event'].browse(event_id)
#  
#         if data_event.product_id:
#             if not partner_invoice_id:
#                 data['training_authorization'] = False
#                 data['unit_price'] = self.pool.get('product.product').price_get(cr, uid, [data_event.product_id.id], context=context)[data_event.product_id.id]
#                 return {'value':data}
#             data_partner = self.pool.get('res.partner').browse(cr, uid, partner_invoice_id)
#             context.update({'partner_id':data_partner and data_partner.id})
#             data['unit_price'] = self.pool.get('product.product').price_get(cr, uid, [data_event.product_id.id], context=context)[data_event.product_id.id]
#             return {'value':data}
#         return {'value':data}

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    case_id = fields.Many2many('event.registration', 'move_line_registration', 'move_line_id', 'reg_id', string='Registration')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: