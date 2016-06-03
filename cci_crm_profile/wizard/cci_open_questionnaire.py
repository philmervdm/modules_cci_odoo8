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

from openerp import models, fields , api

class open_questionnaire(models.TransientModel):
    _inherit  = 'open.questionnaire'

    @api.model
    def default_get(self,fields):
        res = super(open_questionnaire, self).default_get(fields)
        if res.get('question_ans_ids',False):
            final_result = []
            que_obj = self.env['crm_profiling.question']
            for r in res['question_ans_ids']:
                open = que_obj.browse(r['question_id']).open_question
                r.update({'chek_open_question':open})
                final_result.append(r)
            res['question_ans_ids'] = final_result
        return res
    
    @api.multi
    def questionnaire_compute(self):
        """ Adds selected answers in partner form """
        model = self.env.context.get('active_model')
        answers = []
        if model == 'res.partner':
            for d in self.question_ans_ids:
                 if d.answer_id:
                     answers.append(d.answer_id.id)
                 else:
                    vals = {
                        'name': '/',
                        'question_id': d.question_id.id,
                        'text': d.open_answer
                    }
                    answer_id = self.env['crm_profiling.answer'].create(vals)
                    answers.append(answer_id.id)
            self.env[model]._questionnaire_compute(answers)
        return {'type': 'ir.actions.act_window_close'}
    
class open_questionnaire_line(models.TransientModel):
    _inherit = 'open.questionnaire.line'
    
    @api.one
    @api.depends('question_id','question_id.open_question')
    def check_open_question(self):
        if self.question_id.open_question:
            self.chek_open_question = True
        else:
            self.chek_open_question = False
            
    open_answer = fields.Text('Open Answer')
    chek_open_question = fields.Boolean(compute='check_open_question',string='Check Open?')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

