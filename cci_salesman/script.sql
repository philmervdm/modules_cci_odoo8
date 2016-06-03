CREATE OR REPLACE VIEW actions_commercials_par_types AS
SELECT cc.name, rph.action, rph.date
FROM res_partner_history rph
	INNER JOIN cci_contact cc
		ON rph.cci_contact = cc.id;
		
CREATE OR REPLACE VIEW res_partner_interest_full AS
SELECT * FROM res_partner_interest
UNION
SELECT * FROM res_partner_interest_next;

CREATE OR REPLACE VIEW actions_commerciales_par_produits AS
SELECT cp.name AS product, cc.name AS contact, rpi.date
FROM res_partner_interest_full rpi
	INNER JOIN cci_contact cc
		ON rpi.cci_contact = cc.id
	INNER JOIN cci_product cp
		ON rpi.product = cp.id;

CREATE OR REPLACE VIEW ca_par_produit AS
SELECT cc.name AS contact,
	cp.name AS product,
	ail.write_date AS date_facture,
	ail.price_subtotal AS facture,
	sol.write_date AS date_bdc,
	sol.product_uos_qty * sol.price_unit AS bdc
FROM cci_product cp
	INNER JOIN cci_product_category cpc
		ON cp.id = cpc.cci_product
	INNER JOIN product_product pp
		ON pp.id = cpc.product
	INNER JOIN account_invoice_line ail
		ON pp.id = ail.product_id
	INNER JOIN account_invoice ai
		ON ail.invoice_id = ai.id
	INNER JOIN res_users ru
		ON ru.id = ai.user_id
	INNER JOIN cci_contact cc
		ON cc.user = ru.id
	INNER JOIN sale_order_line sol
		ON sol.product_id = pp.id
	INNER JOIN sale_order so
		ON so.id = sol.order_id;