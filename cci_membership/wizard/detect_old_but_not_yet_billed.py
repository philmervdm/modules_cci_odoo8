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
import datetime
from openerp import api, fields, models, _
from openerp.exceptions import Warning
from openerp.osv.orm import except_orm


class detect_old_but_not_yet_billed(models.TransientModel):
    _name = 'detect.old.but.not.yet.billed'

    current_year = fields.Integer(string='Current Year',
                                  default=int(datetime.datetime.today().strftime('%Y')), required=True)
    from_year = fields.Integer(string='From (membership year)',
                               default=int(datetime.datetime.today().strftime('%Y'))-1, required=True)
    to_year = fields.Integer(string='To (membership year)',
                             default=int(datetime.datetime.today().strftime('%Y'))-1, required=True)
    ignore_if_creditnote = fields.Boolean(string='Ignore if refund',
                                          help='Ignore if partner has credit nota that cancel the bill(s) of the last year')
    ignore_if_not_in_activity = fields.Boolean(string='Ignore if partner not in activity')
    ignore_if_refuse = fields.Boolean(string="Ignore if partner noted as 'Refuse membership'")
    ignore_if_free_or_associated = fields.Boolean(string="Ignore if Free or Associated")

    @api.multi
    def search_partners(self):
        result = {'state': 'end'}
        from_year = min(self.from_year, self.to_year)
        to_year = max(self.from_year, self.to_year)
        selection = "SELECT id FROM product_template \
                    WHERE membership_year BETWEEN %s AND %s" % (str(from_year), str(to_year))
        self.env.cr.execute(selection)
        res = self.env.cr.fetchall()
        if len(res) > 0:
            prod_ids = [x[0] for x in res]
            journal = self.env['account.journal'].search([('type', '=', 'sale')])
            jnl_ids = journal.ids
            if len(jnl_ids) > 0:
                current_year = self.current_year
                selection = "SELECT id FROM product_template WHERE membership_year = %s" % str(current_year)
                self.env.cr.execute(selection)
                res = self.env.cr.fetchall()
                if len(res) > 0:
                    current_prod_ids = [x[0] for x in res]
                    selection = """SELECT distinct partner_id FROM account_move_line 
                                       WHERE product_id in (%s) AND journal_id in (%s)
                                """  % (','.join([str(x) for x in prod_ids]),','.join([str(x) for x in jnl_ids]))
                    self.env.cr.execute(selection)
                    res = self.env.cr.fetchall()
                    partner_ids = [x[0] for x in res]
                    if self.ignore_if_not_in_activity:
                        ignore_partner_ids = self.env['res.partner'].search(['|', ('state_id', '<>', 1),
                                                                             ('active', '=', False)])
                        partner_ids = [x for x in partner_ids if x not in ignore_partner_ids.ids]
                    if self.ignore_if_refuse:
                        ignore_partner_ids = self.env['res.partner'].search([('refuse_membership', '=', True)])
                        partner_ids = [x for x in partner_ids if x not in ignore_partner_ids.ids]
                    if self.ignore_if_free_or_associated:
                        ignore_partner_ids = self.env['res.partner'].search(['|', ('free_member', '=', True),
                                                                             ('associate_member', '<>', False)])
                        partner_ids = [x for x in partner_ids if x not in ignore_partner_ids.ids]
                    # remove all billed this year : doesn't take refund into account : a bill has been created, it's enought
                    selection = """SELECT distinct partner_id 
                                       FROM account_move_line 
                                       WHERE product_id in (%s) AND journal_id in (%s)
                                """  % (','.join([str(x) for x in current_prod_ids]),','.join([str(x) for x in jnl_ids]))
                    self.env.cr.execute( selection )
                    res = self.env.cr.fetchall()
                    if res:
                        current_partner_ids = [x[0] for x in res]
                        partner_ids = [x for x in partner_ids if x not in current_partner_ids]
                    if self.ignore_if_creditnote:
                        # extract all concerned partners
                        # search of all partners with refund invoices on membership products last_year
                        #  then, for each of then cacul of what is billed and what is refund to take into account or not
                        selection = "SELECT id FROM product_template WHERE membership_year = %s" % str(to_year)
                        self.env.cr.execute(selection)
                        res = self.env.cr.fetchall()
                        if len(res) > 0:
                            prod_ids = [x[0] for x in res]
                            jnl_ids = self.env['account.journal'].search([('type', '=', 'sale')])
                            if len(jnl_ids) > 0:
                                selection = """SELECT partner_id, SUM( debit ), SUM( credit )
                                                   FROM account_move_line 
                                                   WHERE product_id in (%s) AND journal_id in (%s)
                                                   GROUP by partner_id
                                            """  % (','.join([str(x) for x in prod_ids]),','.join([str(x) for x in jnl_ids]))
                                self.env.cr.execute(selection)
                                res = self.env.cr.fetchall()
                                ignore_partner_ids = []
                                for line in res:
                                    if line[1] > 0 and (line[2] - line[1] < 0.1):
                                        # we have canceled the bill(s) by the refund(s) last year => ignore this partner
                                        ignore_partner_ids.append(line[0])
                                partner_ids = [x for x in partner_ids if x not in ignore_partner_ids]
                    result = {
                        'name': _("Partners"),
                        'view_type': 'form',
                        'view_mode': 'tree,form',
                        'res_model': 'res.partner',
                        'domain': "[('id', 'in', [%s])]" % ','.join([str(x) for x in partner_ids]),
                        'type': 'ir.actions.act_window'
                    }
                else:
                    raise Warning(_('Empty Selection !'),
                                  _('No membership products found for the current year.'))
            else:
                raise Warning(_('Empty Selection !'),
                              _('No sale journal found.'))
        else:
            raise Warning(_('Empty Selection !'),
                          _('No membership products for years between %s and %s, so no selection possible.') % (str(from_year),str(to_year)))
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
