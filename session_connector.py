# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from openerp.osv import osv
from openerp.osv import fields
from datetime import date
import time
import pdb
import pymysql
import logging

_logger = logging.getLogger(__name__)

class session_connector(osv.osv):
    """ Connector Session class """
    _name = "session.connector"
    _description = "Session Connector VirtueMart"
    _columns = {
        'host': fields.char('Host', size=64, required=True),
        'user': fields.char('User', size=64, required=True),
        'pwd': fields.char('Password', size=64, required=True),
        'dbname': fields.char('DB Name', size=64, required=True),
        'port': fields.integer('Port',required=True),
    }

    def insert_orders(self,cr,uid,dict_parms):

	order_obj = self.pool.get('sale.order')
	partner_obj = self.pool.get('res.partner')

	conn = pymysql.connect(host=dict_parms['host'],user=dict_parms['user'],\
				passwd=dict_parms['pwd'],db=dict_parms['dbname'])
	#conn = pymysql.connect(host=dict_parms['host'],port=dict_parms['port'],user=dict_parms['user'],\
	#			passwd=dict_parms['pwd'],db=dict_parms['dbname'])
	cur = conn.cursor(pymysql.cursors.DictCursor)
	
	cur.execute("select date(created_on) as fecha,vz3vx_virtuemart_orders.* from vz3vx_virtuemart_orders")
	contador = 0
	index = 0
	for r in cur.fetchall():
		print(index)
		index = index + 1
		order_id = 0
		order_id = order_obj.search(cr,uid,[('virtuemart_order_id','=',int(r['virtuemart_order_id']))])
		partner_id = partner_obj.search(cr,uid,[('virtuemart_user_id','=',r['virtuemart_user_id'])])

		if not partner_id:
			# raise osv.except_osv("ERROR", "Problema de sincronización con maestro de clientes")
			print("ERROR Problema de sincronización con maestro de clientes")
			continue

		vals_order = {
			'virtuemart_order_id': r['virtuemart_order_id'],
			'amount_untaxed': float(r['order_subtotal']),
			'amount_tax': float(r['order_tax']),
			'amount_total': float(r['order_total']),
			'date_order': str(r['fecha']),
			'note': r['oc_note'].decode('cp1252'),
			'partner_id': partner_id[0],
			'pricelist_id': 1,
			'picking_policy': 'direct',
			'warehouse_id': 1,
			'partner_invoice_id': partner_id[0],
			'partner_shipping_id': partner_id[0],
			}
		if not order_id:
			order_id = order_obj.create(cr,uid,vals_order)

	_logger.info(str(date.today())+" - Interface VirtueMart - Fin carga ordenes")
	conn.close()


    def insert_order_lines(self,cr,uid,dict_parms):

	order_obj = self.pool.get('sale.order')
	order_line_obj = self.pool.get('sale.order.line')
	partner_obj = self.pool.get('res.partner')
	product_obj = self.pool.get('product.product')
	
	conn = pymysql.connect(host=dict_parms['host'],user=dict_parms['user'],\
				passwd=dict_parms['pwd'],db=dict_parms['dbname'])
	#conn = pymysql.connect(host=dict_parms['host'],port=dict_parms['port'],user=dict_parms['user'],\
	#			passwd=dict_parms['pwd'],db=dict_parms['dbname'])
	cur = conn.cursor(pymysql.cursors.DictCursor)
	
	cur.execute("select * from vz3vx_virtuemart_order_items")
	contador = 0
	product_id_unknown = product_obj.search(cr,uid,[('default_code','=','UNKNOWN')])
	# pdb.set_trace()
	for r in cur.fetchall():
		print contador
		contador = contador + 1
		order_id = 0
		order_ids = order_obj.search(cr,uid,[('virtuemart_order_id','=',r['virtuemart_order_id'])])
		order_line_ids = order_line_obj.search(cr,uid,[('virtuemart_order_id','=',r['virtuemart_order_item_id'])])
		product_id = product_obj.search(cr,uid,[('virtuemart_product_id','=',int(r['virtuemart_product_id']))])

		if not product_id:
			product_id = product_id_unknown
		
		for order in order_obj.browse(cr,uid,order_ids):
			oerp_id = order.id

		# if not order_ids or not product_id:
		# 	print "Problema de sincronización con ordenes de venta"
		#	sys.exit(8)
		# pdb.set_trace()
		vals_order_line = {
			'order_id': oerp_id,
			'product_id': product_id[0],
			'name': r['order_item_name'].decode('cp1252'),
			'price_unit': float(r['product_item_price']),
			'product_uom_qty': float(r['product_quantity']),
			'price_subtotal': float(r['product_final_price']),
			'virtuemart_order_id': int(r['virtuemart_order_item_id'])
			}
		if not order_line_ids:
			order_line_id = order_line_obj.create(cr,uid,vals_order_line)

	_logger.info(str(date.today())+" - Interface VirtueMart - Fin carga lineas de ordenes")
	conn.close()





    def update_customers(self,cr,uid,dict_parms):
	
	partner_obj = self.pool.get('res.partner')
	conn = pymysql.connect(host=dict_parms['host'],user=dict_parms['user'],\
				passwd=dict_parms['pwd'],db=dict_parms['dbname'])
	#conn = pymysql.connect(host=dict_parms['host'],port=dict_parms['port'],user=dict_parms['user'],\
	#	passwd=dict_parms['pwd'],db=dict_parms['dbname'])
	cur = conn.cursor(pymysql.cursors.DictCursor)
	
	cur.execute("select * from vz3vx_virtuemart_userinfos")

	index = 0	
	for r in cur.fetchall():
		print index
		index = index + 1
		# import pdb;pdb.set_trace()
		partner_id = 0
		partner_id = partner_obj.search(cr,uid,[('virtuemart_user_id','=',r['virtuemart_user_id'])])
		if not r['first_name']:
			r['first_name'] = ''
		if not r['middle_name']:
			r['middle_name'] = ''
		vals_partner = {
				'company_id': 1,
				'name': r['last_name'].decode('cp1252')+', '+r['first_name'].decode('cp1252')+' '+r['middle_name'].decode('cp1252'),
				'active': True,
				'customer': True,
				'street': r['address_1'].decode('cp1252'),
				'city': r['city'],
				'phone': r['phone_1'],
				'fax': r['fax'],
				'zip': r['zip'],
				# 'email': r['user_email'],	
				'virtuemart_user_id': r['virtuemart_user_id'],
				'is_company': True,
				}
		if not partner_id:
			# import pdb;pdb.set_trace()
			# try:
			partner_id = partner_obj.create(cr,uid,vals_partner,context = {})
			# except:
			# raise osv.except_osv("ERROR", "No se pudo insertar un cliente")
			
	_logger.info(str(date.today())+" - Interface VirtueMart - Fin carga clientes")
	conn.close()
	return True


    def update_productos(self,cr,uid,dict_parms):
	product_obj = self.pool.get('product.product')
	template_obj = self.pool.get('product.template')

	conn = pymysql.connect(host=dict_parms['host'],user=dict_parms['user'],\
		passwd=dict_parms['pwd'],db=dict_parms['dbname'])
	#conn = pymysql.connect(host=dict_parms['host'],port=dict_parms['port'],user=dict_parms['user'],\
	#	passwd=dict_parms['pwd'],db=dict_parms['dbname'])
	cur = conn.cursor(pymysql.cursors.DictCursor)
	
	cur.execute("select a.*,b.* from vz3vx_virtuemart_products a inner join vz3vx_virtuemart_products_es_es b on a.virtuemart_product_id = b.virtuemart_product_id")

	index = 0	
	for r in cur.fetchall():
		# import pdb;pdb.set_trace()
		_logger.debug('Insertando %s'%r['product_name'].decode('cp1252'))
		print(index)
		index = index + 1
		product_id = 0
		template_id = 0
		# product_id = product_obj.search(cr,uid,[('virtuemart_product_id','=',int(r['product_id']))])
		product_id = product_obj.search(cr,uid,[('virtuemart_product_id','=',int(r['virtuemart_product_id']))])
		

		vals = {
			'categ_id': 1,
			'cost_method': 'standard',
			'type': 'consu',
			'uom_id': 1,
			'uom_po_id': 1,
			'default_code': r['product_sku'],
			'name': r['product_name'].decode('cp1252'),
			'description': r['product_desc'].decode('cp1252'),
			'purchase_ok': True,
			'sale_ok': True,
			'code': r['virtuemart_product_id'],
			'active': True,
			'virtuemart_product_id': int(r['virtuemart_product_id'])
			}
		if not product_id:
			product_id = product_obj.create(cr,uid,vals)
	conn.close()
	_logger.info(str(date.today())+" - Interface VirtueMart - Fin carga productos")

	return True



    def transfer_virtuemart(self,cr,uid,ids=None,context=None):

	connection_obj = self.pool.get('session.connector')
	connector_ids = connection_obj.search(cr,uid,[('id','>',0)])
	dict_connector = {}
	for connector in connection_obj.browse(cr,uid,connector_ids):
		dict_connector['host'] = connector.host
		dict_connector['dbname'] = connector.dbname
		dict_connector['port'] = connector.port
		dict_connector['user'] = connector.user
		dict_connector['pwd'] = connector.pwd
		# upd_producto = self.update_productos(cr,uid,dict_connector)
		# upd_customers = self.update_customers(cr,uid,dict_connector)
		# ins_orders = self.insert_orders(cr,uid,dict_connector)
		ins_order_lines = self.insert_order_lines(cr,uid,dict_connector)

session_connector()

