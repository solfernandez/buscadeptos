import os
from main import Publicacion
from bs4 import BeautifulSoup

THIS_DIR = os.path.dirname(os.path.realpath(__file__))

def test_argenprop_extraer_de_listado():
    p1 = Publicacion(url='https://argenprop.com.ar/departamento-en-alquiler-en-palermo-hollywood-3-ambientes--14152793',
                     description='Honduras 6000, Piso 10',
                     price='USD 480',
                     location='Palermo Hollywood, Palermo',
                     pub_id='14152793',
                     descartado=False)
    with open(os.path.join(THIS_DIR, "listado_argenprop.html")) as f:
        pubs = argenprop_extraer_de_listado(html=f.read())
        assert pubs[0] == p1
