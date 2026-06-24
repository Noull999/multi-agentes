#!/bin/bash
# 🤖 Multi-Agentes — Lanzador rápido
# Uso: ./agente.sh
# También: ./agente.sh review|support|consultor [args...]

BOT_DIR="/root/multi-agentes"
VENV="source .venv/bin/activate"

show_menu() {
    clear
    echo "╔══════════════════════════════════════════╗"
    echo "║     🤖  MULTI-AGENTES - MENÚ            ║"
    echo "╠══════════════════════════════════════════╣"
    echo "║  OpenCode Go · CrewAI · 3 herramientas   ║"
    echo "╚══════════════════════════════════════════╝"
    echo ""
    echo "  1) 🔍 Code Review     — Analizar código fuente"
    echo "  2) 🛠️  IT Support      — Diagnosticar problema IT"
    echo "  3) 🎯 Consultor       — Generar propuesta + código"
    echo "  q) Salir"
    echo ""
}

run_review() {
    local ruta="$1"
    local modelo="${2:-kimi-k2.7-code}"
    cd "$BOT_DIR/code-review-bot"
    eval "$VENV"
    python src/main.py "$ruta" --opencode --model "$modelo"
}

run_support() {
    local problema="$1"
    local modelo="${2:-deepseek-v4-flash}"
    cd "$BOT_DIR/it-support-bot"
    eval "$VENV"
    python src/main.py "$problema" --opencode --model "$modelo"
}

run_consultor() {
    local input="$1"
    local modelo="${2:-kimi-k2.7-code}"
    cd "$BOT_DIR/consultor-bot"
    eval "$VENV"
    python src/main.py --input "$input" --opencode --model "$modelo"
}

# Command-line mode
if [ "$1" = "review" ]; then
    run_review "$2" "$3"
    exit $?
elif [ "$1" = "support" ]; then
    run_support "$2" "$3"
    exit $?
elif [ "$1" = "consultor" ]; then
    run_consultor "$2" "$3"
    exit $?
fi

# Interactive menu
while true; do
    show_menu
    read -p "  Opción: " op
    case $op in
        1)
            read -p $'\n📁 Ruta del proyecto: ' ruta
            [ -z "$ruta" ] && continue
            [ ! -d "$ruta" ] && echo "❌ No existe" && sleep 2 && continue
            run_review "$ruta"
            echo ""; read -p "Enter para continuar..."
            ;;
        2)
            read -p $'\n💻 Describe el problema: ' prob
            [ -z "$prob" ] && continue
            run_support "$prob"
            echo ""; read -p "Enter para continuar..."
            ;;
        3)
            echo ""
            echo "📝 Describe el proyecto/cliente (termina con EOF):"
            desc=""
            while IFS= read -r line; do
                [ "$line" = "EOF" ] && break
                desc="$desc$line"$'\n'
            done
            [ -z "$desc" ] && continue
            run_consultor "$(echo "$desc" | head -c 2000)"
            echo ""; read -p "Enter para continuar..."
            ;;
        q|Q) echo -e "\n👋 Hasta luego!"; exit 0 ;;
        *) echo "❌ Opción inválida"; sleep 1 ;;
    esac
done
