# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
from datetime import date
import time

class cci_product(models.Model):
    _name = 'cci.product'

    name = fields.Char(string='Produit', required=True)
    categories = fields.One2many('cci.product.category', 'cci_product',
                                  string='Categories')
    commissioned = fields.Boolean(string='Commissionned')
    order_type = fields.Selection([('participation', 'Participation Club'),
                                    ('order', 'Devis'),
                                    ('membership', 'Adhesion')],
                                   string='Type de BDC')
    product_ids = fields.One2many('product.product', 'cci_product_id', string='Produits comptables associes')
    code = fields.Char('Code',size=12, required=True)
    active = fields.Boolean(string ='Active', default=True)
    
    
class product_product(models.Model):
    _inherit = 'product.product'
    
    cci_product_id = fields.Many2one('cci.product', string='Produit commercial associe')


class cci_product_category(models.Model):
    _name = 'cci.product.category'

    name = fields.Char(string='Categorie', required=True)
    cci_product = fields.Many2one('cci.product', string='Produit', required=True)
    active = fields.Boolean(string='Active', default=True)
        #'product': fields.many2one('product.product', 'Intitule comptable', 
        #                           required=True),

class crm_case(models.Model):
    _inherit = 'crm.lead'
    
    product = fields.Many2one('cci.product', string='Produit')
    product_category = fields.Many2one('cci.product.category', string = 'Categorie')
    partner_contact_id = fields.Many2one('res.partner', string='Contact Person')

class cci_contact(models.Model):
    _name = 'cci.contact'
    
    @api.model
    def _get_year(self):
        today = date.today()
        currentYear = today.strftime("%Y")
        yearTab = []
        
        for i in xrange(int(currentYear) + 2, int(currentYear) - 2, -1):
            yearTab.append((str(i), str(i)))

        return tuple(yearTab)
    
    @api.multi
    def _get_commission(self, year):
        res= {}
        #effacement de la table
        commission_obj = self.env['res.commission']
        all_com_ids = commission_obj.search([])
        all_com_ids.unlink()

        ## prendre tout les product_obj commissionne
        cci_product_obj = self.env['cci.product']
        cci_product_ids = cci_product_obj.search([('commissioned', '=', True)])
        
        lines = []
        real_tot = obj_tot = com1_tot = com2_tot = 0

        #if view tree
        if  len(self) != 1: 
            return res
        
        #obtenir le user_id
        cci_contact_obj = self.env['cci.contact']
#         cci_contact = self[0].read(['id','user'])
        searched_user_id = self.user and self.user.id or False 

        commissions = []
        for cci_product_id in cci_product_ids:
            objective = com1 = com2 = 0
            self.env.cr.execute("""
                SELECT SUM(ail.price_subtotal) as amount
                FROM account_invoice_line ail,
                    account_invoice ai,
                    product_product pp,
                    cci_product cp
                WHERE ail.invoice_id = ai.id
                    AND ail.product_id = pp.id
                    AND pp.cci_product_id = cp.id
                    AND cp.commissioned is true
                    AND ai.user_id = %d
                    AND cp.id = %d
                    AND date_part('year', ai.date_invoice) = %d
                """ % (searched_user_id, cci_product_id.id, int(year)))
            lines = self.env.cr.fetchall()
            if None in lines[0]:
                del lines[0]

            realised = 0
            if len(lines) > 0:  
                realised = int(lines[0][0] or 0)
                
            #find objective
            objective_obj = self.env['cci.objectif']
            obj_id = objective_obj.search([('cci_contact_id', '=', self.id),
                                                    ('year', '=', year),
                                                    ('cci_product', '=', cci_product_id.id)])
            if len(obj_id) == 1:
                objective = obj_id[0].objective
                obj_id = obj_id[0]
            else:
                data_objectif = {'cci_contact_id': self.id,
                        'year': year,
                        'cci_product': cci_product_id.id,
                        'objective' : 0}
                obj_id = objective_obj.create(data_objectif)
            
            #calcul des totaux et des com
            real_tot += realised
            obj_tot += objective
            
            if realised <= objective:
                com1 = realised * 0.015
                com1_tot += realised * 0.015
            else: 
                com2 = realised * 0.025
                com2_tot += realised * 0.025
            
            data = {'product': cci_product_id.id,
                    'realised': realised,
                    'objectif': objective,
                    'objective_id': obj_id.id,
                    'com1' : com1,
                    'com2' : com2,
                    }
            ctx = self.env.context.copy()
            ctx['read'] = True
            id = commission_obj.with_context(ctx).create(data)

            commissions.append(int(id.id))
            
        res.update({'commission': commissions,
                    'realised_total': real_tot,
                    'objective_total': obj_tot,
                    'com1_total': com1_tot,
                    'com2_total': com2_tot
                  })

        return res
    
    @api.onchange('years')
    def onchange_year(self):
        context = dict(self._context or {})
        res = self._get_commission(self.years)
        self.commission = res['commission']
        self.com1_total = 100
    
    @api.multi
    def read(self,fields, load='_classic_read'):
        res = {}
        res = super(cci_contact, self).read(fields, load)
        if 'commission' in fields:
            for com in self:
                year = com.years
                if not year:
                    today = date.today()
                    year = today.strftime("%Y")
            res[0].update(self._get_commission(year))
        return res
    
    @api.multi
    def write(self, data):
        if 'years' in data:
            today = date.today()
            year = today.strftime("%Y")
            data['years'] = year
        return super(cci_contact,self).write(data)

    name = fields.Char(string='Nom', required=True)
    user= fields.Many2one('res.users', string='Utilisateur', required=True)
    years = fields.Selection(_get_year, string='Years')
    commission = fields.One2many('res.commission', 'product', string='Commission')
    realised_total = fields.Float(string='Realise', readonly=True)
    objective_total = fields.Float(string='Objectif',readonly=True)
    com1_total = fields.Float(string='Com (1,5pourcent)', readonly=True)
    com2_total = fields.Float('Com (2,5pourcent)', readonly=True)
    commissioned = fields.Boolean(string='Commissionned')
    active = fields.Boolean(string='Active', default=True)

class res_partner_interest(models.Model):
    _name = 'res.partner.interest'
    
    partner = fields.Many2one('res.partner', string='Partenaire')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    product = fields.Many2one('cci.product', string='Produit')
    cci_contact = fields.Many2one('cci.contact', string='Contact CCI')
    contact = fields.Many2one('res.partner', string='Contact client')
    category = fields.Many2one('cci.product.category', string='Categorie')
    turnover_hoped = fields.Integer(string='CA espere')
    #'orders': fields.function(_get_orders, method=True, type='float', 
    #                          digits=(16, 2), string='BDC'), 
    next_action = fields.Date('Prochaine action')
    cci_contact_follow = fields.Many2one('res.users', 
                                          string ='Contact CCI Suivi')
    description = fields.Char(string='Description/commentaire')
    #'case_id': fields.many2one('crm.case','CRM Case'),
    year = fields.Integer(string='Prospection Year')
    positive = fields.Boolean(string='Positive Conclusion')
    active = fields.Boolean(string='Active', default=True)

class res_partner_history(models.Model):
    _name = 'res.partner.history'
    _rec_name = 'description'

    partner = fields.Many2one('res.partner', string='Partenaire')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    cci_contact = fields.Many2one('cci.contact', string='Contact CCI')
    contact = fields.Many2one('res.partner', string='Contact client')
    action = fields.Selection([
        ('appel_sortant','Appel sortant'),
        ('appel_entrant','Appel entrant'),
        ('commando','Commando'),
        ('mail','Mail'),
        ('site','Site Internet'),
        ('meeting_cci','Meeting CCI'),
        ('meeting_externe','Meeting externe'),
        ('midi','Midi'),
        ('rdv','RDV'),
        ('publication','Publication'),], string='Action')
    # be careful : if you change the definitions here, we must also adapt wizard/extract_actions.py
    # and also in wizard/create_interests.py
    product = fields.Many2one('cci.product', string='Produit')
    category = fields.Many2one('cci.product.category', string='Categorie')
    description = fields.Char(string='Description/commentaire')
    next_action = fields.Date(string ='Prochaine action')
    cci_contact_follow = fields.Many2one('res.users', 
                                          string='Contact CCI Suivi')
    #'case_id': fields.many2one('crm.case','CRM Case'),
    state = fields.Selection([('open','Open'),('closed','Closed')],string='State', default='open')

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    @api.multi
    @api.depends('interest_year')
    def _get_turnover(self):
        res = {}
        for partner in self:
            turnover = 0
            for interest in partner.interest_year:
                turnover += interest.turnover_hoped
            partner.tunover_hoped = turnover
        

    tunover_hoped = fields.Float(compute='_get_turnover')
    history = fields.One2many('res.partner.history', 'partner', string='Historique')
    interest_year = fields.One2many('res.partner.interest', 'partner', string='Marque d\'interet')

class cci_turnover(models.Model):
    _name = 'cci.turnover'
    _rec_name = 'cci_product'
    
    @api.multi
    def read(self, fields=None, load='_classic_read'):

        res = super(cci_turnover, self).read(fields, load)
        if 'details' in fields:
            turnover = self
            detail_obj = self.env['cci.turnover.details']
            
            # remove all details
            all_details = detail_obj.search([])
            all_details.unlink()
            
            self.env.cr.execute("""
                SELECT ai.number, pt.name AS product, ail.price_subtotal, ail.name
                FROM account_invoice ai
                    INNER JOIN account_invoice_line ail
                        ON ai.id = ail.invoice_id
                    INNER JOIN product_product p
                        ON ail.product_id = p.id
                    INNER JOIN cci_product cp
                        ON p.cci_product_id = cp.id
                    INNER JOIN product_template as pt
                        ON p.product_tmpl_id = pt.id
               WHERE cp.id = %s
                    AND ai.partner_id = %s
                    AND date_part('year', ai.date_invoice) = %d 
                    AND ai.state in ('open', 'paid') AND ai.type in ('out_invoice','out_refund')
                """ % (turnover.cci_product.id, 
                       turnover.partner.id,
                       int(turnover.years)))
            lines = self.env.cr.fetchall()
            for line in lines:
                data = {
                        'invoice_number': line[0],
                        'product_name': line[1],
                        'price': line[2],
                        'invoice_line_desc':line[3],
                    }
                detail_id = detail_obj.create(data)
                res[0]['details'].append(detail_id.id)
        
        return res
    
    cci_product = fields.Many2one('cci.product', string='Product', readonly=True)
    sum_price = fields.Float(string='Amount',digits=(16,2), readonly=True)
    partner = fields.Many2one('res.partner', string='Partner', readonly=True)
    details = fields.One2many('cci.turnover.details', 'turnover', string='Details', readonly=True)
    years = fields.Char(string='Year', readonly=True)
    total = fields.Integer(string='Total', readonly=True)

class cci_turnover_details(models.Model):
    _name = 'cci.turnover.details'
    _rec_name = 'product_name'
    
    invoice_number = fields.Char(string='Invoice Number', readonly=True)
    product_name = fields.Char(string='Account product', readonly=True)
    price = fields.Float(string='Amount',digits=(16,2), readonly=True)
    turnover = fields.Many2one('cci.turnover', string='Turnover', readonly=True)
    invoice_line_desc = fields.Char('Invoice Line Description', size=120, readonly=True)


class crm_cci_todo(models.Model):
    _name = 'crm_cci.todo'
    
    model = fields.Char(string='Model') # 'Marque d'intérêt' or 'Historique'
    res_id = fields.Integer(string='Internal Source ID')
    partner = fields.Many2one('res.partner', string='Partenaire')
    date = fields.Date(string='Date')
    product = fields.Many2one('cci.product', string='Produit')
    cci_contact = fields.Many2one('cci.contact', string='Contact CCI')
    contact = fields.Many2one('res.partner', string='Contact client')
    category = fields.Many2one('cci.product.category', string='Categorie')
    turnover_hoped = fields.Integer(string='CA espere')
    next_action = fields.Date(string='Prochaine action')
    cci_contact_follow = fields.Many2one('res.users', string='Contact CCI Suivi')
    description= fields.Char(string='Description/commentaire')
    year = fields.Integer(string='Prospection Year')
    action = fields.Selection([
        ('appel_sortant','Appel sortant'),
        ('appel_entrant','Appel entrant'),
        ('commando','Commando'),
        ('mail','Mail'),
        ('site','Site Internet'),
        ('meeting_cci','Meeting CCI'),
        ('meeting_externe','Meeting externe'),
        ('midi','Midi'),
        ('rdv','RDV'),
        ('publication','Publication'),
        ('/','Aucune')], string='Action')
    state = fields.Selection([('open','Open'),('closed','Closed')], string='State')
    company_phone = fields.Char(string='Company Phone')
    prof_phone = fields.Char(string='Prof. Phone')
    mobile = fields.Char(string='Mobile')
    company_email = fields.Char(string='Company EMail')
    prof_email = fields.Char(string='Prof. Email')
    positive = fields.Boolean(string='Positive Conclusion')

    _order = 'next_action'
    
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
    def convert_phone(self,string):
        PHONE_COUNTRY_PREFIX = self.get_phone_country_prefix()
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
    def onchange_contact(self, contact):
        if contact:
            job_obj = self.env['res.partner']
            job = job_obj.browse([contact])[0]
            pphone = self.convert_phone(job.phone )
            if job.contact_id:
                pemail = job.email  or ''
            else:
                pemail = ''
#             if job.address_id:
#                 cphone = self.convert_phone(job.phone )
#                 cemail = job.email or ''
#             else:
#                 cphone = ''
#                 cemail = ''
            if job.contact_id:
                pmobile = self.convert_phone(job.mobile )
            else:
                pmobile = ''
        else:
            cphone = ''
            pphone = ''
            cemail = ''
            pemail = ''
            pmobile = ''
        return {'value':{#'company_phone': cphone,
                         'prof_phone': pphone,
                         'mobile': pmobile,
                         #'company_email': cemail,
                         'prof_email': pemail,
                }}
    
    @api.model
    def _onlydigits(self,string):
        result = ''
        string = string or ''
        for carac in string:
            if carac in '0123456789':
                result += carac
        return result

    @api.model
    def action_dial_company_phone(self):
        '''Function called by the button 'Dial' next to the 'company_phone' field'''
        erp_number = self._onlydigits(self.company_phone)
        self.env['escaux.server'].dial(erp_number)
    
    @api.model
    def action_dial_prof_phone(self):
        '''Function called by the button 'Dial' next to the 'prof_phone' field'''
        erp_number = self._onlydigits(self.prof_phone)
        self.env['escaux.server'].dial(erp_number)
    
    @api.model
    def action_dial_mobile(self):
        '''Function called by the button 'Dial' next to the 'mobile' field'''
        erp_number = self._onlydigits(self.mobile)
        self.env['escaux.server'].dial(erp_number)

    @api.multi
    def write(self, vals):
        # first, we record all changes other than changes of state
        res_id = False
        
        todo_obj = self.env['crm_cci.todo']
        todo = self[0]

        # for the write, sometimes, we must give the same data because these data are mandatory to record the changes
        if todo.model == u"Marque d'intérêt":
            interest_obj = self.env['res.partner.interest']
            interest = interest_obj.browse(todo.res_id )[0]
            new_vals = vals.copy()
            if 'state' in vals and vals['state'] == 'closed':
                new_vals['active'] = False
            else:
                new_vals['active'] = True
            if 'product' not in new_vals and interest.product:
                new_vals['product'] = interest.product.id
            if 'category' not in new_vals and interest.category:
                new_vals['category'] = interest.category.id
            if 'turnover_hoped' not in new_vals and interest.turnover_hoped:
                new_vals['turnover_hoped'] = interest.turnover_hoped
            if 'cci_contact_follow' not in new_vals and interest.cci_contact_follow:
                new_vals['cci_contact_follow'] = interest.cci_contact_follow.id
            if 'company_phone' in new_vals:
                del new_vals['company_phone']
            if 'prof_phone' in new_vals:
                del new_vals['prof_phone']
            if 'company_email' in new_vals:
                del new_vals['company_email']
            if 'prof_email' in new_vals:
                del new_vals['prof_email']
            if 'mobile' in new_vals:
                del new_vals['mobile']
            if 'state' in new_vals:
                del new_vals['state']
            if 'action' in new_vals:
                del new_vals['action']
            result = interest.write(new_vals)
        elif todo.model == u"Historique":
            histo_obj = self.env['res.partner.history']
            histo = histo_obj.browse(todo.res_id )[0]
            new_vals = vals.copy()
            if 'action' in vals and vals['action'] == '/':
                new_vals['action'] = 'appel_sortant'
            if 'product' not in new_vals and histo.product:
                new_vals['product'] = histo.product.id
            if 'category' not in new_vals and histo.category:
                new_vals['category'] = histo.category.id
            if 'cci_contact_follow' not in new_vals and histo.cci_contact_follow:
                new_vals['cci_contact_follow'] = histo.cci_contact_follow.id
            if 'company_phone' in new_vals:
                del new_vals['company_phone']
            if 'prof_phone' in new_vals:
                del new_vals['prof_phone']
            if 'mobile' in new_vals:
                del new_vals['mobile']
            if 'prof_email' in new_vals:
                del new_vals['prof_email']
            if 'company_email' in new_vals:
                del new_vals['company_email']
            if 'year' in new_vals:
                del new_vals['year']
            if 'turnover_hoped' in new_vals:
                del new_vals['turnover_hoped']
            if 'positive' in new_vals:
                del new_vals['positive']
            result = histo.write(new_vals)
        # record the changes in the todo table
        res = super(crm_cci_todo, self).write(vals)
        # perhaps changes in phone or emails to save on rights objects
        # we record this AFTER the possible change of job
#         todo = todo_obj.browse()
        partner_obj = self.env['res.partner']
        if 'prof_phone' in vals:
            if todo.contact and todo.contact.id > 0:
                result = todo.contact.write({'phone':self._onlydigits(vals['prof_phone'])})
        if 'mobile' in vals:
            if todo.contact and todo.contact.contact_id and todo.contact.contact_id.id > 0:
                result = todo.contact.contact_id.write({'mobile':self._onlydigits(vals['mobile'])})
        if 'prof_email' in vals:
            if todo.contact and todo.contact.id > 0:
                result = todo.contact.write({'email':vals['prof_email']})
#         if 'company_phone' in vals:
#             if todo.contact and todo.contact.address_id and todo.contact.address_id.id > 0:
#                 result = partner_obj.write(cr,uid,[todo.contact.address_id.id],{'phone':self._onlydigits(vals['company_phone'])})
#         if 'company_email' in vals:
#             if todo.contact and todo.contact.address_id and todo.contact.address_id.id > 0:
#                 result = partner_obj.write(cr,uid,[todo.contact.address_id.id],{'email':vals['company_email']})
        return res

class account_account(models.Model):
    _inherit = 'account.account'

    cci_commission = fields.Boolean(string='CCI Commission')
