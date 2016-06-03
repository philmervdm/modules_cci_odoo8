# -*- coding: utf-8 -*-
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
# 2012-01-13 Philmer correct the selected address for the invoice : 'invoice', else 'default' else first one
# 2012-02-07 Philmer select only active addresses with SQL SELECT
from openerp import api, fields, models, _
from openerp.exceptions import Warning


class wizard_extend_invoice_membership(models.TransientModel):
    _name = 'wizard.extend.invoice.membership'

    product = fields.Many2one('product.product', string='Membership product', required=True)
    site_product_id = fields.Many2one('product.product', string='Site product', required=True)

    @api.multi
    def invoice_membership(self):
        partner_ids = self.env.context.get('active_ids')
        product_id = self.product
        site_product_id = self.site_product_id
        self.env.cr.execute('''
                SELECT parent_id, id, type
                FROM res_partner
                WHERE active = true AND parent_id IN (%s)
                ORDER by parent_id
                ''' % ','.join([str(i) for i in partner_ids]))
        fetchal = self.env.cr.fetchall()
        if not fetchal and len(partner_ids) <= 1:
            raise Warning(_('Error !'),
                          _('No Address defined for this partner'))
        partner_address_ids = {}
        for x in range(len(fetchal)):
            pid = fetchal[x][0]
            id = fetchal[x][1]
            type = fetchal[x][2]
            if partner_address_ids.has_key(pid):
                if type == 'invoice':
                    partner_address_ids[pid] = {'id': id, 'type': type}
                elif type == 'default' and partner_address_ids[pid]['type'] != 'invoice':
                        partner_address_ids[pid] = {'id': id, 'type': type}
            else:
                partner_address_ids[pid] = {'id': id, 'type': type}
        # check if all selected partners have an address, else the invoicing will fail
        partners_wo_address = []
        for pid in partner_ids:
            if not partner_address_ids.has_key(pid):
                partners_wo_address.append(pid)
        invoice_list= []
#         if partners_wo_address:
#             raise Warning(_('Error !'),
#                           _('Some partners have no address (%s) !' % ','.join([str(id) for id in partners_wo_address]) ))
#         else:
        invoice_obj = self.env['account.invoice']
        partner_obj = self.env['res.partner']
        product_obj = self.env['product.product']
        invoice_line_obj = self.env['account.invoice.line']
        invoice_tax_obj = self.env['account.invoice.tax']
        product = product_id.read(['uom_id', 'description', 'description_sale'])[0]
        site_product = site_product_id.read(['uom_id', 'description', 'description_sale'])[0]
        desc_site_prod = desc_prod = ''
        if product['description']:
            desc_prod = product['description']
        else:
            desc_prod = product['description_sale'] or ''
        if site_product['description']:
            desc_site_prod = site_product['description']
        else:
            desc_site_prod = site_product['description_sale'] or ''
        for partner_id in partner_ids:
            # check if there is a membership amount on the partner
            # if not, ignore this partner and display a message only if this partner is the only invoiced one
            partner_data = partner_obj.browse(partner_id).read(['membership_amount','site_membership', 'desc_add_site'])[0]
            membership_amount = partner_data['membership_amount']
            if membership_amount:
                suppl_sites = partner_data['site_membership'] or 0
                desc_site = partner_data['desc_add_site'] or ''
                account_id = partner_obj.browse(partner_id).read(['property_account_receivable'])['property_account_receivable'][0]
                read_fpos = partner_obj.browse(partner_id).read(['property_account_position'])
                fpos_id = read_fpos['property_account_position'] and read_fpos['property_account_position'][0]
                line_value = {'product_id': product_id}
                quantity = 1
                line_dict = invoice_line_obj.product_id_change(product_id.id, product['uom_id'][0], quantity, '', 'out_invoice', partner_id, fpos_id)
                line_value.update(line_dict['value'])
                if line_value['invoice_line_tax_id']:
                    tax_tab = [(6, 0, line_value['invoice_line_tax_id'])]
                    line_value['invoice_line_tax_id'] = tax_tab
                address_id = 0
                if partner_address_ids.has_key(partner_id):
                    address_id = partner_address_ids[partner_id]['id']
                invoice_id = invoice_obj.create({
                    'name': '',
                    'partner_id': partner_id,
                    'account_id': account_id,
                    'fiscal_position': fpos_id or False
                    }
                )
                line_value['invoice_id'] = invoice_id.id
                line_value['price_unit'] = membership_amount
                line_value['note'] = desc_prod
                #membership_amount =  partner_obj.read(cr, uid, partner_id, ['membership_amount'])['membership_amount']
                #if membership_amount:
                #    line_value['price_unit'] = membership_amount
                invoice_line_id = invoice_line_obj.create(line_value)
                if suppl_sites:
                    site_line_value = {
                        'product_id': site_product_id.id,
                        }
                    site_line_dict = invoice_line_obj.product_id_change(site_product_id.id, site_product['uom_id'][0], suppl_sites, '', 'out_invoice', partner_id, fpos_id)
                    site_line_value.update(site_line_dict['value'])
                    if site_line_value['invoice_line_tax_id']:
                        tax_tab = [(6, 0, site_line_value['invoice_line_tax_id'])]
                        site_line_value['invoice_line_tax_id'] = tax_tab
                    site_line_value['invoice_id'] = invoice_id.id
                    site_line_value['quantity'] = suppl_sites
                    if '<desc>' in desc_site_prod:
                        site_line_value['note'] = desc_site_prod.replace('<desc>', desc_site)
                    else:
                        site_line_value['note'] = desc_site_prod
                    site_line_id = invoice_line_obj.create(site_line_value)
                    invoice_id.write({'invoice_line': [(6, 0, [invoice_line_id.id, site_line_id])]})
                else:
                    invoice_id.write({'invoice_line': [(6, 0, [invoice_line_id.id])]})
                invoice_list.append(invoice_id.id)
                if line_value['invoice_line_tax_id']:
                    tax_value = invoice_id.compute().values()
                    for tax in tax_value:
                        invoice_tax_obj.create(tax)
            else:
                if len(partner_ids) == 1:
                    raise Warning(_('Warning !'), 
                                  _('No invoice created, because this partner has an empty membership amount !'))
        value = {
                'domain': [
                    ('id', 'in', invoice_list),
                    ],
                'name': _('Membership invoice'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.invoice',
                'type': 'ir.actions.act_window',
                'context': {'type': 'out_invoice'},
            }
        return value

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
