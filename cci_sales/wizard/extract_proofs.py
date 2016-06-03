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
from openerp import models, fields, api, _

import base64
from xlwt import *

class wizard_extract_proof(models.TransientModel):
    _name = 'wizard.extract.proof'
    
    choice = fields.Selection([('all','Devis et bons de commande'),
                               ('selected','Seulement les bons de commande confirmés')],
                              string ='Selection', required = True, default = 'all')

    @api.multi
    def get_file(self, data):
        res = {}
        proofs = []
        obj_sol = self.env['sale.order.line']
        sol_ids = obj_sol.search([('adv_issue','in',data['active_ids'])] )
        if sol_ids:
            sales_lines = obj_sol.read(sol_ids,['order_id'])
            so_ids = []
            for sol in sales_lines:
                so_ids.append(sol['order_id'][0])
            if so_ids:
                obj_so = self.env['sale.order']
                if self.choice == 'all':
                    states = ['manual','progress','draft']
                else:
                    states = ['manual','progress']
                selected = []
                saleorders = obj_so.read(so_ids,['id','state'])
                for sorder in saleorders:
                    if sorder['state'] in states:
                        selected.append(sorder['id'])
                if selected:
                    obj_proof = self.env['sale.advertising.proof']
                    proof_ids = obj_proof.search([('target_id','in',selected)])
                    if proof_ids:
                        proofs = obj_proof.browse(proof_ids)
        wb1 = Workbook()
        ws1 = wb1.add_sheet('Preuves de parution')
        ws1.write(0,0,'contact')
        ws1.write(0,1,'company_name')
        ws1.write(0,2,'street')
        ws1.write(0,3,'street2')
        ws1.write(0,4,'zip_code')
        ws1.write(0,5,'zip_loc')
        ws1.write(0,6,'order_name')
        ws1.write(0,7,'order_state')
        line = 1
        if proofs:
            for proof in proofs:
                count = proof.number or 1
                for i in range(0,count):
                    ws1.write(line,0,proof.name or '')
                    ws1.write(line,1,proof.target_id.partner_id.name or '')
                    ws1.write(line,2,proof.address_id.street or '')
                    ws1.write(line,3,proof.address_id.street2 or '')
                    ws1.write(line,4,proof.address_id.zip_id.name or '')
                    ws1.write(line,5,proof.address_id.zip_id.city or '')
                    ws1.write(line,6,proof.target_id.name or '')
                    ws1.write(line,7,proof.target_id.state or '')
                    line += 1
            msg ='Save the File with '".xls"' extension.'
        else:
            msg ='No proofs found for this issue.'
        res.update({'msg': msg})
        wb1.save('proofs.xls')
        result_file = open('proofs.xls','rb').read()

        # give the result to the user
        res.update({'proofs': base64.encodestring(result_file)})
        result = {
            'name': _('Notification'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.extract.proof2',
            'target': 'new',
            'context': {'res':res, 'name': 'proofs.xls'},
            'type': 'ir.actions.act_window'
        }
        return result
    
class wizard_extract_proof2(models.TransientModel):
    _name = 'wizard.extract.proof2'
    
    msg = fields.Text(string ='File Created', readonly=True)
    proofs = fields.Binary(string= 'Prepared file', readonly=True)
    name = fields. Char(string ='File Name')
    
    @api.model
    def default_get(self,fields):
        res = super(wizard_extract_proof2, self).default_get(fields)
        context = dict(self._context or {})
        res.update({
            'msg': context['res']['msg'],
            'proofs': context['res']['proofs'],
            'name': 'proofs.xls'
        })
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

