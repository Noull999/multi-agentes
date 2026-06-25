"""Tool: parallel multi-source web search (DDG + Wikipedia + StackOverflow + SuperUser + Brave)."""

import json
import os
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from crewai.tools import tool


# ─── HTTP helper ───────────────────────────────────────────────────────────────

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


def _fetch_json(url: str, headers: dict | None = None, timeout: int = 10) -> dict | list | None:
    req = urllib.request.Request(url, headers=headers or _DEFAULT_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return None


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text).strip()


# ─── Sources ───────────────────────────────────────────────────────────────────

def _search_duckduckgo(query: str) -> list[dict]:
    """DuckDuckGo Instant Answer API — sin clave, respuestas de conocimiento."""
    url = (
        f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}"
        "&format=json&no_html=1&skip_disambig=1"
    )
    data = _fetch_json(url)
    if not data:
        return []

    results = []
    if data.get("AbstractText") and data.get("AbstractURL"):
        results.append({
            "source": "DDG",
            "title": data.get("Heading", query)[:80],
            "url": data["AbstractURL"],
            "snippet": data["AbstractText"][:300],
        })
    for topic in (data.get("RelatedTopics") or [])[:5]:
        if "Text" in topic and "FirstURL" in topic:
            text = topic["Text"]
            results.append({
                "source": "DDG",
                "title": text.split(" - ")[0][:80],
                "url": topic["FirstURL"],
                "snippet": text[:200],
            })
        elif "Topics" in topic:
            for sub in topic["Topics"][:2]:
                if "Text" in sub and "FirstURL" in sub:
                    results.append({
                        "source": "DDG",
                        "title": sub["Text"].split(" - ")[0][:80],
                        "url": sub["FirstURL"],
                        "snippet": sub["Text"][:200],
                    })
    return results


def _search_wikipedia(query: str) -> list[dict]:
    """Wikipedia Search API — sin clave, excelente para conceptos técnicos."""
    url = (
        "https://en.wikipedia.org/w/api.php?action=query&list=search"
        f"&srsearch={urllib.parse.quote(query)}&srlimit=3&format=json&utf8=1"
    )
    data = _fetch_json(url)
    if not data:
        return []

    results = []
    for item in (data.get("query", {}).get("search") or [])[:3]:
        title = item.get("title", "")
        snippet = _strip_html(item.get("snippet", ""))
        if title:
            results.append({
                "source": "Wikipedia",
                "title": title,
                "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}",
                "snippet": snippet[:250],
            })
    return results


def _search_stackoverflow(query: str) -> list[dict]:
    """StackOverflow — sin clave, ideal para errores de software y código."""
    url = (
        "https://api.stackexchange.com/2.3/search/advanced"
        f"?q={urllib.parse.quote(query)}&site=stackoverflow"
        "&pagesize=4&order=desc&sort=relevance&accepted=True"
    )
    data = _fetch_json(url)
    if not data:
        return []

    results = []
    for item in (data.get("items") or [])[:4]:
        title = item.get("title", "")
        link = item.get("link", "")
        if title and link:
            results.append({
                "source": "StackOverflow",
                "title": title,
                "url": link,
                "snippet": (
                    f"Votos: {item.get('score', 0)} | "
                    f"Respuestas: {item.get('answer_count', 0)} | "
                    f"Tags: {', '.join(item.get('tags', [])[:4])}"
                ),
            })
    return results


def _search_superuser(query: str) -> list[dict]:
    """SuperUser (StackExchange) — sin clave, enfocado en soporte IT de usuario final."""
    url = (
        "https://api.stackexchange.com/2.3/search/advanced"
        f"?q={urllib.parse.quote(query)}&site=superuser"
        "&pagesize=4&order=desc&sort=relevance&accepted=True"
    )
    data = _fetch_json(url)
    if not data:
        return []

    results = []
    for item in (data.get("items") or [])[:4]:
        title = item.get("title", "")
        link = item.get("link", "")
        if title and link:
            results.append({
                "source": "SuperUser",
                "title": title,
                "url": link,
                "snippet": (
                    f"Votos: {item.get('score', 0)} | "
                    f"Respuestas: {item.get('answer_count', 0)}"
                ),
            })
    return results


def _search_brave(query: str) -> list[dict]:
    """Brave Search API — requiere BRAVE_API_KEY (2000 búsquedas/mes gratis)."""
    api_key = os.getenv("BRAVE_API_KEY", "").strip()
    if not api_key:
        return []
    url = f"https://api.search.brave.com/res/v1/web/search?q={urllib.parse.quote(query)}&count=5"
    data = _fetch_json(url, headers={
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": api_key,
    })
    if not data:
        return []

    results = []
    for item in (data.get("web", {}).get("results") or [])[:5]:
        title = item.get("title", "")[:80]
        url_val = item.get("url", "")
        snippet = item.get("description", "")[:250]
        if title and url_val:
            results.append({
                "source": "Brave",
                "title": title,
                "url": url_val,
                "snippet": snippet,
            })
    return results


# ─── Main tool ─────────────────────────────────────────────────────────────────

@tool("WebSearch")
def web_search(query: str) -> str:
    """
    Busca simultáneamente en múltiples fuentes: DuckDuckGo, Wikipedia, StackOverflow y SuperUser.
    Si BRAVE_API_KEY está configurada, también incluye Brave Search.
    Devuelve resultados combinados, deduplicados y ordenados por fuente.
    """
    sources = [
        _search_duckduckgo,
        _search_wikipedia,
        _search_stackoverflow,
        _search_superuser,
    ]
    if os.getenv("BRAVE_API_KEY", "").strip():
        sources.append(_search_brave)

    all_results: list[dict] = []
    errors: list[str] = []

    with ThreadPoolExecutor(max_workers=len(sources)) as executor:
        futures = {executor.submit(fn, query): fn.__name__ for fn in sources}
        for future in as_completed(futures, timeout=15):
            name = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                errors.append(f"{name}: {e}")

    # Deduplicar por URL
    seen: set[str] = set()
    unique: list[dict] = []
    for r in all_results:
        url = r.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(r)

    if not unique:
        msg = f"No se encontraron resultados para: '{query}'"
        if errors:
            msg += f"\nErrores: {'; '.join(errors)}"
        return msg

    # Agrupar por fuente para el resumen
    source_counts: dict[str, int] = {}
    for r in unique:
        src = r.get("source", "?")
        source_counts[src] = source_counts.get(src, 0) + 1

    sources_summary = " · ".join(f"{s}({n})" for s, n in source_counts.items())
    output = f"🔍 Búsqueda multi-fuente: **{query}**\n"
    output += f"📊 {len(unique)} resultados — {sources_summary}\n\n"

    for i, r in enumerate(unique[:12], 1):
        title = r.get("title", "Sin título")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        source = r.get("source", "?")
        output += f"{i}. **[{source}] {title}**\n"
        if url:
            output += f"   🔗 {url}\n"
        if snippet:
            output += f"   > {snippet}\n"
        output += "\n"

    if errors:
        output += f"\n⚠️ Fuentes con error: {'; '.join(errors)}"

    return output


# ─── Knowledge base tool (sin cambios) ────────────────────────────────────────

@tool("SearchKnowledgeBase")
def search_knowledge_base(issue_type: str, symptoms: str) -> str:
    """
    Busca en una base de conocimiento local de problemas IT comunes.
    Devuelve soluciones conocidas basadas en tipo de problema y síntomas.
    Útil cuando el problema es conocido y tiene una solución documentada.
    """
    kb = {
        "internet": {
            "no_connection": (
                "1. Verificar que el cable de red/WiFi esté conectado\n"
                "2. Ejecutar: ipconfig /release && ipconfig /renew (Windows)\n"
                "3. Ejecutar: sudo systemctl restart NetworkManager (Linux)\n"
                "4. Ping a 8.8.8.8 para verificar conectividad básica\n"
                "5. Verificar que el router esté encendido y sin luces rojas"
            ),
            "slow": (
                "1. Medir velocidad con speedtest.net\n"
                "2. Cerrar aplicaciones que consuman ancho de banda\n"
                "3. Verificar que no haya descargas activas\n"
                "4. Reiniciar router: desconectar 30 segundos\n"
                "5. Si persiste, contactar al ISP"
            ),
            "dns": (
                "1. ipconfig /flushdns (Windows) o sudo systemd-resolve --flush-caches (Linux)\n"
                "2. Cambiar DNS a 8.8.8.8 (Google) o 1.1.1.1 (Cloudflare)\n"
                "3. Verificar que el servicio DNS esté corriendo\n"
                "4. Probar con nslookup google.com"
            ),
        },
        "hardware": {
            "no_video": (
                "1. Verificar que el monitor esté encendido y conectado\n"
                "2. Probar otro cable HDMI/DisplayPort\n"
                "3. Probar otro puerto en la tarjeta gráfica\n"
                "4. Escuchar si la PC hace beeps (código POST)\n"
                "5. Resentar la RAM y tarjeta gráfica"
            ),
            "overheating": (
                "1. Limpiar el polvo de ventiladores y disipadores\n"
                "2. Verificar que todos los ventiladores giren\n"
                "3. Aplicar pasta térmica nueva al procesador\n"
                "4. Mejorar flujo de aire en el gabinete\n"
                "5. Monitorear temperaturas con HWMonitor"
            ),
            "no_boot": (
                "1. Verificar que el cable de poder esté bien conectado\n"
                "2. Escuchar beeps y buscar el código POST\n"
                "3. Probar la fuente de poder (test con multímetro o PSU tester)\n"
                "4. Resentar RAM, GPU, cables de datos\n"
                "5. Probar boot con mínimo necesario (1 RAM, sin GPU si tiene integrada)"
            ),
        },
        "software": {
            "blue_screen": (
                "1. Anotar el código de error (ej: 0x0000001A)\n"
                "2. Buscar el código en: https://www.google.com\n"
                "3. Revisar Event Viewer > Windows Logs > System\n"
                "4. Verificar controladores recién instalados\n"
                "5. Ejecutar: sfc /scannow (Windows) o memtest86 (RAM)"
            ),
            "virus": (
                "1. Desconectar de la red inmediatamente\n"
                "2. Boot en modo seguro con red\n"
                "3. Ejecutar Windows Defender completo online\n"
                "4. Ejecutar Malwarebytes o AdwCleaner\n"
                "5. Revisar programas en inicio: msconfig (Windows) o systemctl (Linux)"
            ),
            "slow_computer": (
                "1. Revisar Task Manager > procesos que más CPU/RAM usan\n"
                "2. Deshabilitar programas de inicio innecesarios\n"
                "3. Liberar espacio en disco (>15% libre recomendado)\n"
                "4. Ejecutar limpieza de disco: cleanmgr (Windows)\n"
                "5. Verificar que no sea malware\n"
                "6. Considerar upgrade a SSD si usa HDD"
            ),
            "printer": (
                "1. Verificar que la impresora esté encendida y con papel\n"
                "2. Verificar conexión USB o WiFi\n"
                "3. Revisar colas de impresión: cancelar documentos atascados\n"
                "4. Reinstalar driver desde la web del fabricante\n"
                "5. Windows: Ejecutar solucionador de problemas de impresión"
            ),
        },
        "network": {
            "no_ping": (
                "1. Verificar que el firewall no esté bloqueando ICMP\n"
                "2. Windows: netsh advfirewall firewall add rule name='ICMP Allow' protocol=icmpv4:8,any dir=in action=allow\n"
                "3. Linux: sudo ufw allow icmp\n"
                "4. Verificar reachability con traceroute/tracert"
            ),
            "vpn": (
                "1. Verificar credenciales VPN\n"
                "2. Probar con otro protocolo (OpenVPN / WireGuard / IKEv2)\n"
                "3. Verificar que el puerto necesario no esté bloqueado\n"
                "4. Revisar logs del cliente VPN\n"
                "5. Probar desde otra red para descartar firewall local"
            ),
        },
    }

    issue_type = issue_type.lower().strip()
    symptoms = symptoms.lower().strip()

    if issue_type in kb:
        for key, solution in kb[issue_type].items():
            key_words = key.replace("_", " ").split()
            if all(word in symptoms for word in key_words):
                return (
                    f"📚 *Base de Conocimiento — {issue_type}: {key}*\n\n"
                    f"Síntomas detectados: {symptoms}\n\n"
                    f"Solución documentada:\n{solution}"
                )

    available = []
    for category, issues in kb.items():
        for issue in issues:
            available.append(f"  • {category}: {issue.replace('_', ' ')}")
    return (
        f"No encontré una entrada exacta para '{issue_type}: {symptoms}'.\n"
        f"Entradas disponibles en la KB:\n" + "\n".join(available)
    )
