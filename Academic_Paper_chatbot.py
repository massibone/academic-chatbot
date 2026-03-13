"""
Academic Paper Chatbot
======================
Cerca paper accademici su Semantic Scholar e risponde a domande
usando l'API gratuita di Semantic Scholar + la logica Python.

Requisiti:
    pip install requests

"""

import requests
import textwrap


# ─── Configurazione ────────────────────────────────────────────────────────────

BASE_URL = "https://api.semanticscholar.org/graph/v1"

FIELDS_PAPER = "title,abstract,year,authors,citationCount,url,fieldsOfStudy"

SEPARATOR = "─" * 60


# ─── Funzioni di ricerca ───────────────────────────────────────────────────────

def search_papers(query: str, limit: int = 5) -> list[dict]:
    """
    Cerca paper su Semantic Scholar per parola chiave.

    Args:
        query: termine di ricerca (es. "machine learning public sector")
        limit: numero massimo di risultati da restituire

    Returns:
        Lista di dizionari con i dati dei paper trovati
    """
    url = f"{BASE_URL}/paper/search"
    params = {
        "query": query,
        "limit": limit,
        "fields": FIELDS_PAPER,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])

    except requests.exceptions.ConnectionError:
        print("  [ERRORE] Nessuna connessione internet.")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"  [ERRORE] API ha risposto con errore: {e}")
        return []
    except Exception as e:
        print(f"  [ERRORE] Problema inatteso: {e}")
        return []


def get_paper_details(paper_id: str) -> dict | None:
    """
    Recupera i dettagli completi di un singolo paper tramite il suo ID.

    Args:
        paper_id: identificativo Semantic Scholar del paper

    Returns:
        Dizionario con i dettagli del paper, oppure None se non trovato
    """
    url = f"{BASE_URL}/paper/{paper_id}"
    params = {"fields": FIELDS_PAPER + ",references,citations"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()

    except Exception as e:
        print(f"  [ERRORE] Impossibile recuperare il paper: {e}")
        return None


# ─── Funzioni di visualizzazione ──────────────────────────────────────────────

def format_authors(authors: list[dict]) -> str:
    """Restituisce i nomi degli autori come stringa leggibile."""
    if not authors:
        return "Autori non disponibili"
    nomi = [a.get("name", "N/D") for a in authors[:3]]  # max 3 autori
    if len(authors) > 3:
        nomi.append(f"e altri {len(authors) - 3}")
    return ", ".join(nomi)


def print_paper(paper: dict, indice: int) -> None:
    """Stampa a schermo le informazioni di un paper in modo leggibile."""
    titolo = paper.get("title", "Titolo non disponibile")
    anno = paper.get("year", "Anno sconosciuto")
    autori = format_authors(paper.get("authors", []))
    citazioni = paper.get("citationCount", 0)
    abstract = paper.get("abstract") or "Abstract non disponibile."
    url = paper.get("url", "")
    campi = paper.get("fieldsOfStudy") or []

    # Tronca l'abstract a 300 caratteri per leggibilità
    abstract_corto = textwrap.shorten(abstract, width=300, placeholder="...")

    print(f"\n  [{indice}] {titolo}")
    print(f"      Autori   : {autori}")
    print(f"      Anno     : {anno}  |  Citazioni: {citazioni}")
    if campi:
        print(f"      Settori  : {', '.join(campi)}")
    print(f"      Abstract : {abstract_corto}")
    if url:
        print(f"      Link     : {url}")


def print_separator() -> None:
    print(f"\n{SEPARATOR}")


# ─── Logica del chatbot ────────────────────────────────────────────────────────

def handle_search(query: str, papers_cache: list) -> list:
    """
    Gestisce il comando di ricerca, aggiorna la cache dei paper trovati.

    Args:
        query: termine da cercare
        papers_cache: lista dove salvare i paper trovati

    Returns:
        Lista aggiornata dei paper trovati
    """
    print(f"\n  Cerco paper su: '{query}'...")
    results = search_papers(query, limit=5)

    if not results:
        print("  Nessun paper trovato. Prova con termini diversi.")
        return []

    print(f"\n  Trovati {len(results)} paper:\n")
    for i, paper in enumerate(results, start=1):
        print_paper(paper, i)

    return results


def handle_detail(papers_cache: list) -> None:
    """
    Chiede all'utente quale paper approfondire e mostra i dettagli completi.

    Args:
        papers_cache: lista dei paper trovati nell'ultima ricerca
    """
    if not papers_cache:
        print("  Prima esegui una ricerca con il comando 'cerca'.")
        return

    try:
        scelta = int(input("\n  Numero del paper da approfondire: "))
        if not 1 <= scelta <= len(papers_cache):
            print(f"  Inserisci un numero tra 1 e {len(papers_cache)}.")
            return
    except ValueError:
        print("  Inserisci un numero valido.")
        return

    paper = papers_cache[scelta - 1]
    paper_id = paper.get("paperId")

    if not paper_id:
        print("  ID paper non disponibile.")
        return

    print(f"\n  Recupero dettagli per: {paper.get('title', '')}...")
    dettagli = get_paper_details(paper_id)

    if not dettagli:
        return

    # Stampa dettagli completi
    print_separator()
    print_paper(dettagli, scelta)

    citazioni_in = dettagli.get("citations", [])
    riferimenti = dettagli.get("references", [])
    print(f"\n      Citato da : {len(citazioni_in)} paper")
    print(f"      Cita      : {len(riferimenti)} paper")
    print_separator()


def handle_summary(papers_cache: list) -> None:
    """
    Genera un riassunto testuale dei paper trovati nell'ultima ricerca.

    Args:
        papers_cache: lista dei paper trovati nell'ultima ricerca
    """
    if not papers_cache:
        print("  Prima esegui una ricerca con il comando 'cerca'.")
        return

    print("\n  ─── RIASSUNTO DEI PAPER TROVATI ───\n")

    anni = [p.get("year") for p in papers_cache if p.get("year")]
    citazioni = [p.get("citationCount", 0) for p in papers_cache]
    campi = set()
    for p in papers_cache:
        for c in (p.get("fieldsOfStudy") or []):
            campi.add(c)

    print(f"  Numero paper  : {len(papers_cache)}")
    if anni:
        print(f"  Periodo coperto: {min(anni)} - {max(anni)}")
    print(f"  Citazioni totali: {sum(citazioni)}")
    print(f"  Paper più citato: {max(citazioni)} citazioni")
    if campi:
        print(f"  Settori rilevati: {', '.join(sorted(campi))}")

    print("\n  Titoli trovati:")
    for i, p in enumerate(papers_cache, 1):
        print(f"    {i}. {p.get('title', 'N/D')} ({p.get('year', '?')})")


def print_help() -> None:
    """Mostra i comandi disponibili."""
    print("""
  Comandi disponibili:
  ─────────────────────────────────────────
  cerca   → Cerca paper per parola chiave
  dettagli → Approfondisci un paper specifico
  riassunto → Riassumi i paper trovati
  aiuto   → Mostra questo messaggio
  esci    → Esci dal programma
  ─────────────────────────────────────────
    """)


# ─── Loop principale ───────────────────────────────────────────────────────────

def main():
    """Avvia il chatbot accademico."""
    print("\n" + "═" * 60)
    print("  📚 Academic Paper Chatbot")
    print("  Powered by Semantic Scholar API")
    print("  GitHub: massibone")
    print("═" * 60)
    print_help()

    papers_cache = []  # Salva i paper dell'ultima ricerca

    while True:
        try:
            comando = input("  > Comando: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\n  Arrivederci! 👋")
            break

        if not comando:
            continue

        elif comando == "esci":
            print("\n  Arrivederci! 👋\n")
            break

        elif comando == "aiuto":
            print_help()

        elif comando == "cerca":
            query = input("  Parola chiave: ").strip()
            if query:
                papers_cache = handle_search(query, papers_cache)
            else:
                print("  Inserisci un termine di ricerca.")

        elif comando == "dettagli":
            handle_detail(papers_cache)

        elif comando == "riassunto":
            handle_summary(papers_cache)

        else:
            print(f"  Comando '{comando}' non riconosciuto. Digita 'aiuto' per la lista comandi.")

        print_separator()


if __name__ == "__main__":
    main()
