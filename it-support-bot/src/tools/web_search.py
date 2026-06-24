"""Tool: web search for solutions and knowledge base queries."""

import urllib.request
import urllib.parse
import json
import re
from typing import Optional
from crewai.tools import tool


@tool("WebSearch")
def web_search(query: str) -> str:
    """
    Busca en la web soluciones técnicas y documentación.
    Útil para encontrar pasos de troubleshooting, guías y foros de soporte.
    Realiza una búsqueda web real usando DuckDuckGo JSON API.
    """
    encoded = urllib.parse.quote(query)
    url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))

        results = []

        # Abstract / Answer
        abstract = data.get("AbstractText", "")
        abstract_url = data.get("AbstractURL", "")
        if abstract and abstract_url:
            results.append({
                "title": data.get("Heading", "Resultado"),
                "url": abstract_url,
                "snippet": abstract,
            })

        # Related topics
        for topic in data.get("RelatedTopics", []):
            if "Text" in topic and "FirstURL" in topic:
                text = topic.get("Text", "")
                title = text.split(" - ")[0] if " - " in text else text
                results.append({
                    "title": title,
                    "url": topic.get("FirstURL", ""),
                    "snippet": text,
                })
            elif "Topics" in topic:
                for subtopic in topic["Topics"][:3]:
                    if "Text" in subtopic and "FirstURL" in subtopic:
                        text = subtopic.get("Text", "")
                        title = text.split(" - ")[0] if " - " in text else text
                        results.append({
                            "title": title,
                            "url": subtopic.get("FirstURL", ""),
                            "snippet": text,
                        })

        # Results from the web (DuckDuckGo API doesn't always return full results, this is safe fallback)
        if not results and data.get("Results"):
            for r in data["Results"]:
                if "Text" in r and "FirstURL" in r:
                    text = r.get("Text", "")
                    title = text.split(" - ")[0] if " - " in text else text
                    results.append({
                        "title": title,
                        "url": r.get("FirstURL", ""),
                        "snippet": text,
                    })

        if results:
            output = f"🔍 Resultados de búsqueda para: {query}\n\n"
            for i, r in enumerate(results[:8], 1):
                snippet = r.get("snippet", "")
                output += f"{i}. **{r['title']}**\n   {r['url']}\n"
                if snippet:
                    output += f"   > {snippet[:200]}\n"
                output += "\n"
            return output
        else:
            return f"No se encontraron resultados web para: {query}"

    except Exception as e:
        return f"Error en búsqueda web: {e}"


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

    # Buscar en KB
    issue_type = issue_type.lower().strip()
    symptoms = symptoms.lower().strip()

    if issue_type in kb:
        for key, solution in kb[issue_type].items():
            # Require ALL words in the key to appear in symptoms to avoid
            # false positives (e.g. "no" alone matching "no_boot", "no_ping")
            key_words = key.replace("_", " ").split()
            if all(word in symptoms for word in key_words):
                return (
                    f"📚 *Base de Conocimiento — {issue_type}: {key}*\n\n"
                    f"Síntomas detectados: {symptoms}\n\n"
                    f"Solución documentada:\n{solution}"
                )

    # Si no hay match exacto, listar lo disponible
    available = []
    for category, issues in kb.items():
        for issue in issues:
            available.append(f"  • {category}: {issue.replace('_', ' ')}")
    return (
        f"No encontré una entrada exacta para '{issue_type}: {symptoms}'.\n"
        f"Entradas disponibles en la KB:\n" + "\n".join(available)
    )
