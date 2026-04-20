"""
Bot Pagos Venezuela — Repuestos Madriz C.A.
Módulo de cobros: Zelle, Binance/USDT, Pago Móvil.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from shared.db import database as db
from shared.ui import limpiar, pedir, pedir_numero
from shared.pagos import pagos_venezuela as pv

console = Console()

COLORES = {
    "zelle":      "green",
    "binance":    "yellow",
    "pago_movil": "cyan",
}


def menu_nuevo_cobro():
    limpiar()
    console.print(Panel("[bold cyan]Registrar Cobro[/bold cyan]", box=box.ROUNDED))

    console.print("  Método de pago:")
    for k, met in pv.METODOS.items():
        info = pv.METODO_INFO[met]
        color = COLORES.get(met, "white")
        console.print(f"  [bold]{k}.[/bold] [{color}]{info['nombre']}[/{color}]  [dim]({info['moneda']})[/dim]")

    op = pedir("Elige método (1-3)")
    metodo = pv.METODOS.get(op)
    if not metodo:
        console.print("  [red]Opción inválida.[/red]")
        input("\n  Enter para continuar...")
        return

    info = pv.METODO_INFO[metodo]
    console.print(f"\n  [dim]{info['tips']}[/dim]")
    console.print(f"  [dim]Datos necesarios: {info['datos']}[/dim]\n")

    pieza_id = pedir_numero("ID de la pieza (opcional)", requerido=False)
    monto    = pedir_numero(f"Monto en {info['moneda']}")
    notas    = pedir("Notas (cliente, referencia)", requerido=False)

    pago_id = pv.registrar_cobro({
        "pieza_id": int(pieza_id) if pieza_id else None,
        "monto":    monto,
        "metodo":   metodo,
        "estado":   "pendiente",
        "notas":    notas,
    })
    console.print(f"\n  [green]✓ Cobro #{pago_id} registrado como pendiente.[/green]")

    verificar = input("\n  ¿Verificar comprobante por foto ahora? (s/n): ").strip().lower()
    if verificar == "s":
        _verificar_cobro_existente(pago_id, metodo, monto)

    input("\n  Enter para continuar...")


def _verificar_cobro_existente(pago_id: int, metodo: str, monto: float):
    ruta = pedir("Ruta de la foto del comprobante")
    console.print("  [dim]Analizando con Claude Vision...[/dim]")
    try:
        resultado = pv.verificar_comprobante(ruta, metodo, monto)
        color_monto = "green" if resultado["coincide_monto"] else "red"
        color_estado = "green" if resultado["estado_transaccion"] == "completado" else "yellow"
        console.print(Panel(
            f"[bold]Monto detectado:[/bold]  [{color_monto}]{resultado['monto_detectado']:.2f} {resultado['moneda']}[/{color_monto}]\n"
            f"[bold]¿Coincide?:[/bold]       [{color_monto}]{'Sí' if resultado['coincide_monto'] else 'No'}[/{color_monto}]\n"
            f"[bold]Estado:[/bold]           [{color_estado}]{resultado['estado_transaccion']}[/{color_estado}]\n"
            f"[bold]Fecha:[/bold]            {resultado.get('fecha_pago','')}\n"
            f"[bold]Referencia:[/bold]       {resultado.get('referencia','')}\n"
            f"[bold]Remitente:[/bold]        {resultado.get('remitente','')}\n"
            f"[bold]Confianza:[/bold]        {resultado.get('confianza','')}\n"
            f"[bold]Observaciones:[/bold]    {resultado.get('observaciones','')}",
            title="Análisis del comprobante", box=box.ROUNDED
        ))
        if resultado["coincide_monto"] and resultado["estado_transaccion"] == "completado":
            confirmar = input("\n  ¿Confirmar pago? (s/n): ").strip().lower()
            if confirmar == "s":
                pv.confirmar_cobro(pago_id)
                console.print("  [green]✓ Pago confirmado.[/green]")
        else:
            rechazar = input("\n  ¿Rechazar este comprobante? (s/n): ").strip().lower()
            if rechazar == "s":
                pv.rechazar_cobro(pago_id)
                console.print("  [red]✗ Pago rechazado.[/red]")
    except Exception as e:
        console.print(f"\n  [red]Error: {e}[/red]")


def menu_pendientes():
    limpiar()
    console.print(Panel("[bold yellow]Cobros Pendientes[/bold yellow]", box=box.ROUNDED))
    pagos = pv.cobros_pendientes()
    if not pagos:
        console.print("  [green]✓ Sin cobros pendientes.[/green]")
        input("\n  Enter para continuar...")
        return

    t = Table(box=box.ROUNDED, show_lines=True)
    t.add_column("ID",      width=5)
    t.add_column("Método",  width=14)
    t.add_column("Monto",   width=12, justify="right")
    t.add_column("Fecha",   width=19)
    t.add_column("Notas",   width=28)

    for p in pagos:
        color = COLORES.get(p["metodo"], "white")
        nombre = pv.METODO_INFO.get(p["metodo"], {}).get("nombre", p["metodo"])
        t.add_row(
            str(p["id"]),
            f"[{color}]{nombre}[/{color}]",
            f"${p['monto']:.2f}",
            p["fecha"],
            p.get("notas","")
        )
    console.print(t)

    op = input("\n  ¿Verificar alguno por foto? Ingresa ID (o Enter para salir): ").strip()
    if op.isdigit():
        pago = next((p for p in pagos if str(p["id"]) == op), None)
        if pago:
            _verificar_cobro_existente(int(op), pago["metodo"], pago["monto"])
        else:
            console.print("  [red]ID no encontrado.[/red]")
    input("\n  Enter para continuar...")


def menu_convertir_tasa():
    limpiar()
    console.print(Panel("[bold cyan]Convertir USD → VES[/bold cyan]", box=box.ROUNDED))
    monto = pedir_numero("Monto en USD")
    tasa  = pedir_numero("Tasa del día (Bs/USD)")
    ves   = pv.tasa_usd_a_ves(monto, tasa)
    console.print(Panel(
        f"[bold]USD:[/bold] ${monto:.2f}\n"
        f"[bold]Tasa:[/bold] {tasa:.2f} Bs/USD\n"
        f"[bold]VES:[/bold] [green]Bs. {ves:,.2f}[/green]",
        title="Conversión", box=box.ROUNDED
    ))
    input("\n  Enter para continuar...")


def main():
    db.init_db()
    while True:
        limpiar()
        console.print(Panel(
            "[bold white]REPUESTOS MADRIZ C.A.[/bold white]\n[dim]Pagos Venezuela[/dim]",
            box=box.DOUBLE_EDGE, style="green"
        ))
        console.print("  [bold]1.[/bold] Registrar cobro")
        console.print("  [bold]2.[/bold] Ver cobros pendientes")
        console.print("  [bold]3.[/bold] Convertir USD → VES")
        console.print("  [bold]0.[/bold] Salir\n")

        op = input("  Opción: ").strip()
        if   op == "1": menu_nuevo_cobro()
        elif op == "2": menu_pendientes()
        elif op == "3": menu_convertir_tasa()
        elif op == "0":
            console.print("\n  [dim]Hasta luego.[/dim]\n")
            break


if __name__ == "__main__":
    main()
