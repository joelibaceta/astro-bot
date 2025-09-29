import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup
import re
import os
import csv


def make_session() -> requests.Session:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; HoroscopoScraper/1.0; +https://example.org)"
    }
    s = requests.Session()
    s.headers.update(HEADERS)
    retries = Retry(
        total=5, backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=["GET"]
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

def extract_signo_from_h2(texto_h2: str) -> Optional[str]:
    SIGNO_RE = re.compile(r"HOR[ÓO]SCOP[OÓ]\s+DE\s+([A-ZÁÉÍÓÚÜÑ]+)")
    t = texto_h2.strip().upper()
    m = SIGNO_RE.search(t)
    if m:
        return m.group(1).strip()
    return None


def parse_article_html(html: str) -> List[Tuple[str, str]]:
    """
    Parsea el HTML de un artículo y devuelve lista de (signo, prediccion).
    Busca h2 con 'Horóscopo de ...' y obtiene TODOS los párrafos siguientes
    que contengan signos astrológicos.
    """
    soup = BeautifulSoup(html, "html.parser")

    # El contenedor puede cambiar de clase; nos anclamos en 'container__body'
    container = soup.find(
        "div",
        class_=lambda c: c and "container__body" in c
    ) or soup  # si no lo encuentra, usamos todo el documento como fallback

    resultados: List[Tuple[str, str]] = []
    
    # Todos los h2 dentro del contenedor
    for h2 in container.find_all("h2"):
        h2_text = h2.get_text(" ", strip=True).upper()
        
        # Verificar si es un horóscopo
        if not re.search(r"HOR[ÓO]SCOP[OÓ]", h2_text):
            continue
            
        # Patrones para detectar signos astrológicos en el contenido
        SIGNO_PATTERNS = [
            r'ARIES:\s*20\s+MAR\s*-\s*19\s+ABR',
            r'TAURO:\s*20\s+ABR\s*-\s*20\s+MAY',
            r'G[EÉ]MINIS:\s*21\s+MAY\s*-\s*21\s+JUN',
            r'C[AÁ]NCER:\s*22\s+JUN\s*-\s*21\s+JUL',
            r'LEO:\s*22\s+JUL\s*-\s*22\s+AGO',
            r'VIRGO:\s*23\s+AGO\s*-\s*22\s+SET',
            r'LIBRA:\s*23\s+SET\s*-\s*22\s+OCT',
            r'ESCORPIO:\s*23\s+OCT\s*-\s*22\s+NOV',
            r'SAGITARIO:\s*23\s+NOV\s*-\s*22\s+DIC',
            r'CAPRICORNIO:\s*23\s+DIC\s*-\s*21\s+ENE',
            r'ACUARIO:\s*22\s+ENE\s*-\s*17\s+FEB',
            r'PISCIS:\s*18\s+FEB\s*-\s*19\s+MAR'
        ]
        
        # Obtener todos los párrafos siguientes
        current_element = h2.next_sibling
        
        while current_element:
            if hasattr(current_element, 'name') and current_element.name == 'p':
                text = current_element.get_text(" ", strip=True)
                text_clean = re.sub(r"\s+", " ", text).strip()
                
                if text_clean:
                    # Verificar si contiene algún signo
                    for pattern in SIGNO_PATTERNS:
                        match = re.search(pattern, text_clean, re.IGNORECASE)
                        if match:
                            # Extraer el nombre del signo
                            signo_completo = match.group(0)
                            signo_nombre = signo_completo.split(':')[0].strip()
                            
                            # Extraer solo la predicción limpia, eliminando toda la parte inicial redundante
                            # Buscar el patrón completo "SIGNO: DD MMM - DD MMM [:|] " y removerlo
                            texto_limpio = text_clean
                            
                            # Patrón mejorado para capturar: SIGNO: fechas [:|] (incluyendo pipe y dos puntos)
                            patron_completo = rf'{re.escape(signo_nombre)}:\s*\d+\s+[A-Z]+\s*-\s*\d+\s+[A-Z]+\s*[.:|]+\s*'
                            
                            # Remover el patrón completo del inicio
                            texto_limpio = re.sub(f'^{patron_completo}', '', texto_limpio, flags=re.IGNORECASE).strip()
                            
                            # Limpiar cualquier ":" o "|" sobrante al inicio
                            texto_limpio = re.sub(r'^[:|]\s*', '', texto_limpio).strip()
                            
                            # Solo agregar si la predicción no está vacía
                            if texto_limpio:
                                resultados.append((signo_nombre, texto_limpio))
                            break
            
            current_element = current_element.next_sibling
            
            # Si encontramos otro H2, paramos para no mezclar secciones
            if (hasattr(current_element, 'name') and 
                current_element.name == 'h2'):
                break
        
        # Solo procesamos el primer horóscopo que encontremos
        if resultados:
            break

    return resultados

def ensure_csv_with_header(path_csv: str) -> None:
    if not os.path.exists(path_csv) or os.path.getsize(path_csv) == 0:
        with open(path_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["fecha", "signo", "prediccion"])

def append_rows_csv(path_csv: str, rows: List[Tuple[str, str, str]]) -> None:
    if not rows:
        return
    # Filtrar filas con predicciones vacías
    filas_validas = [(fecha, signo, pred) for fecha, signo, pred in rows if pred.strip()]
    if not filas_validas:
        return
    with open(path_csv, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerows(filas_validas)