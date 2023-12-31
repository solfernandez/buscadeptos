import os
import pickle
import requests
import logging
import time
from selenium import webdriver
from dataclasses import dataclass
from bs4 import BeautifulSoup

logger = logging.getLogger()

TIME_BETWEEN_REQUESTS_S = 5


@dataclass
class Publicacion:
    url: str
    description: str
    price: str
    location: str
    pub_id: str
    descartado: bool = False


def get_listado_requests(url):
    headers = {'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/116.0",
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
               "Accept-Encoding": "gzip, deflate, br",
               "Accept-Language": "en,es;q=0.5",
               "DNT": "1",

               }
    return requests.get(url, headers=headers).text


def get_listado_selenium(url):
    browser = get_selenium_driver()
    browser.get(url)
    logger.info("Browsing %s", url)
    html = browser.page_source
    browser.close()
    return html


def zonaprop_extraer_de_listado(html: str) -> list[Publicacion]:
    soup = BeautifulSoup(html, "lxml")
    result = []
    for element in soup.find_all("div", {"data-qa": "posting PROPERTY"}):
        url = "https://www.zonaprop.com.ar" + element.attrs['data-to-posting']
        pub_id = element.attrs['data-id']
        location = element.find(attrs={"data-qa": "POSTING_CARD_LOCATION"}).text
        price = element.find(attrs={"data-qa": "POSTING_CARD_PRICE"}).text
        description = element.find(attrs={"data-qa": "POSTING_CARD_FEATURES"}).text.strip()
        description += " " + element.find(attrs={"data-qa": "POSTING_CARD_DESCRIPTION"}).text.strip()
        pub = Publicacion(url=url, description=description, location=location, price=price, pub_id=pub_id)
        result.append(pub)
    return result


def argenprop_extraer_de_listado(html: str) -> list[Publicacion]:
    soup = BeautifulSoup(html, "lxml")
    result = []
    for element in soup.find_all("div", {"class": "listing__item"}):
        a = element.find_all("a")[0]
        url = "https://argenprop.com.ar" + a.attrs['href']
        pub_id = a.attrs['data-item-card']
        price_el = element.find_all("p", {"class": "card__price"})[0]
        price = " ".join(price_el.text.split()[:2])
        address_el = element.find_all("h2", {"class": "card__address"})[0]
        address = " ".join(address_el.text.split())  # incluir en la description
        location_el = element.find_all("p", {"class": "card__title--primary show-mobile"})[0]
        location = " ".join(location_el.text.split())
        info_el = element.find_all("p", {"class": "card__info"})[0]
        info = " ".join(info_el.text.split())
        description = info + address
        pub = Publicacion(url=url, description=description, location=location, price=price, pub_id=pub_id)
        result.append(pub)
    return result


def load_from_db(db_path) -> dict[str, Publicacion]:
    if not os.path.exists(db_path):
        return {}
    with open(db_path, "rb") as f:
        return pickle.load(f)


def save_to_db(db_path, pubs: dict[str, Publicacion]) -> None:
    with open(db_path, "wb") as f:
        return pickle.dump(pubs, f, protocol=4)


def get_selenium_driver():
    from selenium.webdriver.firefox.options import Options
    options = Options()
    options.set_preference('intl.accept_languages', 'es')
    options.add_argument('-headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    geckodriver_path = "/snap/bin/geckodriver"
    from selenium.webdriver.firefox.service import Service
    driver_service = Service(executable_path=geckodriver_path)
    driver = webdriver.Firefox(options=options, service=driver_service)
    return driver


def send_message(token, chat_id, msg):
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={msg}"
    requests.get(url).json()


def discarded_pub(pub, filters):
    for word in filters:
        if word in pub.description.lower() or word in pub.location.lower():
            return True
    return False


def process(db_path, args, filters):
    urls = [
        (zonaprop_extraer_de_listado,
         "https://www.zonaprop.com.ar/casas-departamentos-ph-alquiler-capital-federal-olivos-florida-mas-de-2-ambientes-mas-50-m2-cubiertos-publicado-hace-menos-de-2-dias-menos-800-dolar-pagina-1.html"),
        (zonaprop_extraer_de_listado,
         "https://www.zonaprop.com.ar/casas-departamentos-ph-alquiler-capital-federal-olivos-florida-mas-de-2-ambientes-mas-50-m2-cubiertos-publicado-hace-menos-de-2-dias-menos-800-dolar-pagina-2.html"),
        (zonaprop_extraer_de_listado,
         "https://www.zonaprop.com.ar/casas-departamentos-ph-alquiler-capital-federal-olivos-florida-mas-de-2-ambientes-mas-50-m2-cubiertos-publicado-hace-menos-de-2-dias-menos-800-dolar-pagina-3.html"),
        (zonaprop_extraer_de_listado,
         "https://www.zonaprop.com.ar/casas-departamentos-ph-alquiler-capital-federal-olivos-florida-mas-de-2-ambientes-mas-50-m2-cubiertos-publicado-hace-menos-de-2-dias-menos-800-dolar-pagina-4.html"),
        (argenprop_extraer_de_listado,
         'https://www.argenprop.com/departamento-alquiler-localidad-capital-federal-localidad-olivos-localidad-florida-vl-1-dormitorio-y-2-dormitorios-y-3-dormitorios-2-ambientes-y-3-ambientes-y-4-ambientes-hasta-800-dolares-desde-50-m2-cubiertos-orden-masnuevos'),
        (argenprop_extraer_de_listado,
         'https://www.argenprop.com/departamento-alquiler-localidad-capital-federal-localidad-olivos-localidad-florida-vl-1-dormitorio-y-2-dormitorios-y-3-dormitorios-2-ambientes-y-3-ambientes-y-4-ambientes-hasta-800-dolares-desde-50-m2-cubiertos-orden-masnuevos-pagina-2'),
        (argenprop_extraer_de_listado,
         'https://www.argenprop.com/departamento-alquiler-localidad-capital-federal-localidad-olivos-localidad-florida-vl-1-dormitorio-y-2-dormitorios-y-3-dormitorios-2-ambientes-y-3-ambientes-y-4-ambientes-hasta-800-dolares-desde-50-m2-cubiertos-orden-masnuevos-pagina-3'),
        (argenprop_extraer_de_listado,
         'https://www.argenprop.com/departamento-alquiler-localidad-capital-federal-localidad-olivos-localidad-florida-vl-1-dormitorio-y-2-dormitorios-y-3-dormitorios-2-ambientes-y-3-ambientes-y-4-ambientes-hasta-800-dolares-desde-50-m2-cubiertos-orden-masnuevos-pagina-4')

    ]

    processing_pubs: list[Publicacion] = []
    for extract_func, url in urls:
        html = get_listado_selenium(url)
        publicaciones = extract_func(html)
        logger.info("Extraidas %d publicaciones", len(publicaciones))
        processing_pubs.extend(publicaciones)
        #if len(publicaciones) < 20:
        #    break
        logger.info("Sleeping for %ds", TIME_BETWEEN_REQUESTS_S)
        time.sleep(TIME_BETWEEN_REQUESTS_S)

    TOKEN = args.TOKEN
    chat_id = args.chat_id
    nuevos = 0
    if processing_pubs:
        stored_pubs = load_from_db(db_path)
        for pub in processing_pubs:
            if pub.pub_id not in stored_pubs and not discarded_pub(pub, filters):
                stored_pubs[pub.pub_id] = pub
                nuevos += 1
                logger.info("Nueva publicacion: %s %s", pub.pub_id, pub.url)
                send_message(TOKEN, chat_id, f"Nueva publicion: {pub.url}. Barrio: {pub.location} Precio: {pub.price}.")
        save_to_db(db_path, stored_pubs)
    logger.info("Nuevos %d", nuevos)


if __name__ == '__main__':
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["list", "process", "bot"])
    parser.add_argument("TOKEN")
    parser.add_argument("chat_id")
    args = parser.parse_args()

    db_path = "pubs.pickle"
    filters = ['temporal', 'temporario', 'temporal', 'amoblado', 'amueblado', 'mataderos', 'liniers', 'versalles', 'barrio norte',
               'recoleta', 'devoto', 'once', 'lugano', 'soldati', 'mataderos', 'villa del parque']

    if args.cmd == "process":
        process(db_path, args, filters)

    elif args.cmd == "list":
        pubs = load_from_db(db_path)
        for pub in pubs.values():
            print(pub)

    elif args.cmd == 'bot':
        TOKEN = args.TOKEN
        chat_id = args.chat_id
        message = "holis"
        send_message(TOKEN, chat_id, message)
