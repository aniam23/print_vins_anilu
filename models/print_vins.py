from odoo import models, fields, api
from odoo.exceptions import UserError
from io import BytesIO
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
import base64
import requests
import re
import logging

_logger = logging.getLogger(__name__)

class PrintVins(models.Model):
    _name = 'print.vins'
    _description = 'Print VIN Labels'
    
    name = fields.Char(string='Name')
    sale_order = fields.Many2one('sale.order', string='Sales Order')
    model_hs7 = fields.Many2many('mrp.production', string='MODEL HS7')
    gvwr = fields.Many2many('vin_generator.gvwr_manager', string='GVWR Related')
    gawr = fields.Many2many('print.gawr', string='GAWR')
    gawr_lb = fields.Float(string='GAWR lb')
    weight_total = fields.Float(string='Total Weight')
    product_name = fields.Char(string='Product Name')
    printer_config_id = fields.Many2one(
        'printer.conf', 
        string='Configuración de Impresora',
        domain="[('active', '=', True)]"
    )
    
    def get_data(self):
        """Gets the VIN of the selected HS7 model"""
        if not self.model_hs7:
            raise UserError("No se ha seleccionado un modelo HS7")
        if not self.model_hs7.vin_dispayed:
            raise UserError("El modelo HS7 seleccionado no tiene un VIN asignado")
        return self.model_hs7.vin_dispayed

    def get_tire_specs(self, product):
        """Gets technical specifications of tires"""
        if not product or not product.bom_ids:
            raise UserError("El producto no tiene lista de materiales configurada")
        
        specs = {
            'tire_rating': None,
            'lbs_wheels': None,
            'rin': None,
            'wheel_names': [],
            'wheels_count': {},
            'ply_pr': None,
            'rim_jante': None,
            'tire_description': None
        }
    
        try:
            bom = product.bom_ids[0]
            llanta_encontrada = False
            
            for bom_line in bom.bom_line_ids:
                if not bom_line.product_id:
                    continue
                    
                nombre = bom_line.product_id.display_name.upper()
                
                if 'LLANTA' in nombre:
                    llanta_encontrada = True
                    partes = [p.strip() for p in nombre.split() if p.strip()]
                    
                    if len(partes) < 2:
                        raise UserError(f"El nombre de la llanta no contiene suficientes datos: {nombre}")
    
                    specs['rin'] = partes[1]
                    specs['wheel_names'].append(nombre)
                    specs['wheels_count'][bom_line.product_id.id] = bom_line.product_qty
                    specs['tire_description'] = nombre
    
                    if len(partes) > 8 and "''" in partes[8] and 'X' in partes[9] and "''" in partes[10]:
                        specs['rim_jante'] = ' '.join(partes[8:11])
                    
                    if len(partes) >= 3:
                        if match := re.search(r'(\d+PLY|\d+PR)', partes[2]):
                            specs['ply_pr'] = match.group(1)
                        else:
                            raise UserError(f"No se encontró el número de capas (PLY/PR) en: {nombre}")
                    else:
                        raise UserError(f"El nombre de la llanta no contiene especificación de capas: {nombre}")
    
                    self.set_tire_ratings(specs, nombre, partes[1])
                    break
                
            if not llanta_encontrada:
                raise UserError("No se encontró ningún componente de tipo LLANTA en la lista de materiales")
    
            campos_obligatorios = ['rin', 'ply_pr', 'rim_jante']
            for campo in campos_obligatorios:
                if not specs[campo]:
                    raise UserError(f"Falta información obligatoria: {campo.upper()}")
    
        except UserError:
            raise  
        except Exception as e:
            raise UserError(f"Error inesperado procesando especificaciones: {str(e)}")
    
        return specs
       
    def set_tire_ratings(self, specs, product_name, rin):
        """Assigns technical specifications based on the tire type and RIN detected from the name."""
        product_name = product_name.upper()
        # Detectar el RIN 
        rin_match = re.search(r'(?:15|16|17\.5)', product_name)
        if not rin_match:
            return  # No se detectó RIN
        rin = rin_match.group()

        # Detectar tipo de llanta con palabras completas
        if re.search(r'\bDUAL\b', product_name):
            tire_type = 'DUAL'
        elif re.search(r'\bSS\b', product_name):
            tire_type = 'SS'
        else:
            tire_type = ''

        # Obtener el mapa de especificaciones desde el modelo
        ratings_map = self.env['tire.specifications'].get_ratings_map()

        # Validar que el RIN exista en el mapa
        if rin not in ratings_map:
            return

        # Obtener grupo de tipo de llanta
        type_group = ratings_map[rin].get(tire_type)
        if not type_group:
            return

        # Buscar coincidencia de PLY/PR en el nombre del producto usando las claves del grupo
        ply_pr = None
        for key in type_group.keys():
            if key in product_name:
                ply_pr = key
                break

        if not ply_pr:
            return  # No se encontró coincidencia de PLY/PR en el nombre

        # Asignar valores si se encuentra el valor correspondiente
        pressure_weight = type_group.get(ply_pr)
        if pressure_weight:
            specs['tire_rating'], specs['lbs_wheels'] = pressure_weight


        
    def prepare_api_data(self):
        """Prepare data for the API"""
        printer_config = self.env['printer.conf'].search([('active', '=', True)], limit=1)
        if not printer_config:
            raise UserError("No hay impresoras configuradas como activas en el sistema")
        
        if not self.model_hs7:
            raise UserError("No se ha seleccionado un modelo HS7")
            
        product = self.model_hs7.product_id
        gvwr = product.gvwr_child or product.gvwr_related
        gawr = product.gawr_related
        
        if not gvwr or not gawr:
            raise UserError("Faltan datos de GVWR o GAWR")
            
        tire_specs = self.get_tire_specs(product)

        gvwr_lb = gvwr.weight_lb
        gvwr_kg = gvwr.weight_kg
        gawr_lb = int(gawr.name[5:8]) if gawr.name and len(gawr.name) >= 8 else 0
        gawr_kg = int(round(gawr_lb * 0.453592))
        weight_lb = product.dry_weight or 0
        carga_maxima_lb = max(weight_lb - gvwr_lb, 0)
        weight_kg = int(round(carga_maxima_lb * 0.453592))
        
        product_name = product.default_code or ""
        model_string = product_name.split(" ")[0].replace('[','').replace(']','') if product_name else ""
        product_vin = self.get_data()
        
        fecha_impresion = (
            self.sale_order.fechapro.strftime('%m/%Y')
            if self.sale_order and hasattr(self.sale_order, 'fechapro') and self.sale_order.fechapro
            else datetime.now().strftime('%m/%Y')
        )
        
        api_data = {
            "ip": printer_config.printer_ip,
            "port": printer_config.printer_port,
            "weight_lb": carga_maxima_lb,
            "weight_kg": weight_kg,
            "lbs_wheels": tire_specs.get('lbs_wheels', ""),
            "rim": tire_specs.get('rin', ""),
            "tire_rating": tire_specs.get('tire_rating', ""),
            "product_vin": product_vin,
            "gvwr_kg": gvwr_kg,
            "fecha_impresion": fecha_impresion,
            "gvwr_lb": gvwr_lb,
            "gawr_kg": gawr_kg,
            "gawr_lb": gawr_lb,
            "rim_jante": tire_specs.get('rim_jante', ""),
            "model_string": model_string,
        }
        return api_data

    def get_active_printer(self):
        """Get the active printer"""
        return self.env['printer.conf'].search([('active', '=', True)], order='sequence', limit=1)

    def send_to_printer_api(self, data):
        """Send data to the printer API"""
        printer = self.get_active_printer()
        if not printer:
            raise UserError("No hay impresoras activas configuradas")
            
        try:
            response = requests.post(
                f"http://{printer.printer_ip}:{printer.printer_port}/print",
                json=data,
                headers={
                    "Content-Type": "application/json"
                },
                timeout=1000
            )
            
            if response.status_code != 200:
                raise UserError(f"Error al imprimir: {response.text}")
                
        except requests.exceptions.RequestException as e:
            raise UserError(f"Error de conexión con la impresora: {str(e)}")

    def print_vins(self):
        """Main action to generate and print VIN labels"""
        print_data = self.prepare_api_data()
        self.send_to_printer_api(print_data)
        
       

    

   
              
