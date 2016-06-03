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
from openerp import models, fields, api
#Old version
#-----------
#class cci_partner_profile_answer(osv.osv):#added for partner.ods
#    _name="cci_partner_profile.answer"
#    _description="Partner Answer"
#    _columns={
#        "partner_id": fields.many2one('res.partner','Partner'),
#        "address_id": fields.many2one('res.partner.address','Address'),
#        "contact_id": fields.many2one('res.partner.contact','Contact'),
#        "question_id": fields.many2one('crm_profiling.question','Question'),
#        "answer_id": fields.many2one('crm_profiling.answer','Answer'),
#        "answer_text":fields.char('Answer Text',size=20)#should be corect
#        }
#cci_partner_profile_answer()


class question(models.Model):
    _inherit="crm_profiling.question"
    
    open_question = fields.Boolean('Open Question')

class answer(models.Model):
    _inherit="crm_profiling.answer"

    text = fields.Text("Open Answer", translate=True)

class partner(models.Model):
    _inherit="res.partner"

    answers_ids =  fields.Many2many('crm_profiling.answer','partner_question_rel','partner','answer','Answers')

#'proxy' classes to give access to many2many tables by XML-RPC
class relation_partner_answer(models.Model):
    _name = 'relation_partner_answer'
    _table = 'partner_question_rel'
    _log_access = False
    
    id = fields.Integer('ID')
    partner = fields.Many2one('res.partner', 'Partner')
    answer = fields.Many2one('crm_profiling.answer', 'Answer')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

