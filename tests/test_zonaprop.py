import os
from main import zonaprop_extraer_de_listado, Publicacion

THIS_DIR = os.path.dirname(os.path.realpath(__file__))


def test_zonaprop_extraer_de_listado():
    p1 = Publicacion(url='https://www.zonaprop.com.ar/propiedades/departamento-2-ambientes-en-palermo-alquiler-temporal-52194077.html',
                     description='58 m²  58 m²  2 amb.  1 dorm.  1 baño Departamento en alquiler temporal. Contrato mínimo 6 meses. Todo incluido. 1 dormitorio con balcón. Cercanía a todos los medios de transporte',
                     price='USD 750', location='Palermo, Capital Federal', pub_id='52194077')
    p2 = Publicacion(url='https://www.zonaprop.com.ar/propiedades/ph-alquiler-flores-52194021.html',
                     description='75 m²  75 m²  3 amb.  2 dorm.  1 baño Ph de 3 ambientes en alquiler. Se ubica en el primer piso por escalera. Cómodo, luminoso y ambientes amplios. En excelente zona comercial. ¡¡sin expensas!!',
                     price='$ 250.000', location='Flores Norte, Flores', pub_id='52194021')
    with open(os.path.join(THIS_DIR, "listado_zonaprop_2_propiedades.html")) as f:
        pubs = zonaprop_extraer_de_listado(html=f.read())
        assert pubs == [p1, p2]