"""
Bot MercadoLibre — Repuestos Madriz C.A.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

from shared.db import database as db
from bot_mercadolibre import mercadolibre as ml

console = Console()


def limpiar():
    os.system("cls" if os.name == "nt" else "clear")


def pedir(texto: str, requerido: bool = True) -> str:
    while True:
        v = input(f"  {texto}: ").strip()
        if v or not requerido:
            return v
        console.print("  [red]Campo requerido.[/red]")


def pedir_numero(texto: str, tipo=float, requerido: bool = True):
    while True:
        raw = pedir(texto, requerido)
        if not raw and not requerido:
            return None
        try:
            return tipo(raw)
        except ValueError:
            console.print("  [red]Ingresa un número válido.[/red]")


def tabla_publicaciones(pubs: list[dict]):
    if not pubs:
        console.print("  [dim]Sin publicaciones.[/dim]")
        return
    t = Table(box=box.ROUNDED, show_lines=True)
    t.add_column("ID",      width=5,  style="dim")
    t.add_column("Pieza",   width=25)
    t.add_column("Título",  width=30)
    t.add_column("Precio",  width=10, justify="right")
    t.add_column("Estado",  width=12)
    t.add_column("ML ID",   width=14, style="dim")
    for p in pubs:
        color = {"publicado":"green","borrador":"yellow","pausado":"red"}.get(p["estado"],"white")
        t.add_row(
            str(p["id"]),
            p.get("pieza_nombre", p.get("nombre","")),
            p["titulo"][:30],
            f"${p['precio']:.2f}",
            f"[{color}]{p['estado']}[/{color}]",
            p.get("ml_item_id","")
        )
    console.print(t)


def menu_nueva_publicacion():
    limpiar()
    console.print(Panel("[bold cyan]Nueva Publicación ML[/bold cyan]", box=box.ROUNDED))
    pieza_id = pedir("ID de la pieza", )
    try:
        pieza_id = int(pieza_id)
    except ValueError:
        console.print("  [red]ID inválido.[/red]")
        input("\n  Enter para continuar...")
        return

    pieza = db.obtener_pieza(pieza_id)
    if not pieza:
        console.print("  [red]Pieza no encontrada.[/red]")
        input("\n  Enter para continuar...")
        return

    console.print(f"  Pieza: [cyan]{pieza['nombre']}[/cyan]")
    console.print("\n  Ingresa rutas de fotos (máx 3). Deja vacío para terminar.")
    fotos = []
    for i in range(1, 4):
        r = pedir(f"Foto {i} (ruta)", requerido=False)
        if not r:
            break
        fotos.append(r)

    if fotos:
        console.print("  [dim]Generando ficha con Claude Vision...[/dim]")
        try:
            ficha = ml.generar_ficha(pieza, fotos)
            console.print(Panel(
                f"[bold]Título:[/bold] {ficha['titulo']}\n"
                f"[bold]Categoría:[/bold] {ficha.get('categoria_sugerida','')}\n"
                f"[bold]Condición:[/bold] {ficha.get('condicion','')}\n\n"
                f"{ficha['descripcion'][:300]}...",
                title="Ficha generada", box=box.ROUNDED
            ))
            titulo = ficha["titulo"]
            descripcion = ficha["descripcion"]
        except Exception as e:
            console.print(f"  [yellow]Vision falló ({e}), ingresa manualmente.[/yellow]")
            titulo = pedir("Título")
            descripcion = pedir("Descripción")
    else:
        titulo = pedir("Título")
        descripcion = pedir("Descripción")

    precio = pedir_numero(f"Precio de publicación (costo: ${pieza['precio_venta']:.2f})")

    pub_id = db.guardar_publicacion_ml({
        "pieza_id":    pieza_id,
        "titulo":      titulo,
        "descripcion": descripcion,
        "precio":      precio,
        "fotos":       fotos,
        "estado":      "borrador"
    })
    console.print(f"\n  [green]✓ Publicación #{pub_id} guardada como borrador.[/green]")

    token = os.environ.get("ML_ACCESS_TOKEN", "")
    if token:
        pub = input("\n  ¿Publicar ahora en MercadoLibre? (s/n): ").strip().lower()
        if pub == "s":
            try:
                resultado = ml.publicar_en_ml(pub_id, token)
                console.print(f"  [green]✓ Publicado: {resultado.get('permalink','')}[/green]")
            except Exception as e:
                console.print(f"  [red]Error al publicar: {e}[/red]")
    else:
        console.print("  [dim]Agrega ML_ACCESS_TOKEN al .env para publicar directamente.[/dim]")

    input("\n  Enter para continuar...")


def menu_verificar_pago():
    limpiar()
    console.print(Panel("[bold cyan]Verificar Pago por Foto[/bold cyan]", box=box.ROUNDED))
    ruta = pedir("Ruta de la foto del comprobante")
    monto = pedir_numero("Monto esperado ($)")
    pieza_id = pedir_numero("ID de la pieza (opcional)", requerido=False)

    console.print("  [dim]Analizando comprobante con Claude Vision...[/dim]")
    try:
        resultado = ml.verificar_pago_foto(ruta, monto)
        color = "green" if resultado["coincide"] else "red"
        console.print(Panel(
            f"[bold]Monto detectado:[/bold]  ${resultado['monto_detectado']:.2f}\n"
            f"[bold]¿Coincide?:[/bold]       [{color}]{'Sí' if resultado['coincide'] else 'No'}[/{color}]\n"
            f"[bold]Método:[/bold]           {resultado.get('metodo_pago','')}\n"
            f"[bold]Fecha:[/bold]            {resultado.get('fecha_pago','')}\n"
            f"[bold]Referencia:[/bold]       {resultado.get('referencia','')}\n"
            f"[bold]Confianza:[/bold]        {resultado.get('confianza','')}\n"
            f"[bold]Observaciones:[/bold]    {resultado.get('observaciones','')}",
            title="Resultado del análisis", box=box.ROUNDED
        ))
        if resultado["coincide"]:
            guardar = input("\n  ¿Registrar este pago como confirmado? (s/n): ").strip().lower()
            if guardar == "s":
                db.registrar_pago({
                    "pieza_id":  int(pieza_id) if pieza_id else None,
                    "monto":     resultado["monto_detectado"],
                    "metodo":    resultado.get("metodo_pago",""),
                    "estado":    "confirmado",
                    "foto_path": ruta,
                    "notas":     resultado.get("referencia","")
                })
                console.print("  [green]✓ Pago registrado.[/green]")
    except Exception as e:
        console.print(f"\n  [red]Error: {e}[/red]")
    input("\n  Enter para continuar...")


def menu_decodificar_vin():
    limpiar()
    console.print(Panel("[bold cyan]Decodificar VIN[/bold cyan]", box=box.ROUNDED))
    vin = pedir("VIN (17 caracteres)")
    console.print("  [dim]Decodificando...[/dim]")
    try:
        info = ml.decodificar_vin(vin)
        if info.get("valido"):
            console.print(Panel(
                f"[bold]Marca:[/bold]         {info['marca']}\n"
                f"[bold]Modelo:[/bold]        {info['modelo']}\n"
                f"[bold]Año:[/bold]           {info['anio']}\n"
                f"[bold]Motor:[/bold]         {info['motor']}\n"
                f"[bold]País:[/bold]          {info['pais_fabricacion']}\n"
                f"[bold]Tipo:[/bold]          {info['tipo_vehiculo']}",
                title=f"VIN: {vin}", box=box.ROUNDED
            ))
            buscar = input("\n  ¿Buscar piezas compatibles en inventario? (s/n): ").strip().lower()
            if buscar == "s":
                termino = f"{info['marca']} {info['modelo']} {info['anio']}"
                from shared.db.database import buscar_piezas
                piezas = buscar_piezas(termino)
                if piezas:
                    from bot_almacen.main import tabla_piezas
                    tabla_piezas(piezas, f"Compatibles con {termino}")
                else:
                    console.print(f"  [dim]Sin piezas para {termino}.[/dim]")
        else:
            console.print("  [red]VIN inválido o no reconocido.[/red]")
    except Exception as e:
        console.print(f"\n  [red]Error: {e}[/red]")
    input("\n  Enter para continuar...")


def menu_publicaciones():
    limpiar()
    pubs = db.todas_publicaciones_ml()
    tabla_publicaciones(pubs)
    input("\n  Enter para continuar...")


def menu_pagos_pendientes():
    limpiar()
    console.print(Panel("[bold yellow]Pagos Pendientes[/bold yellow]", box=box.ROUNDED))
    pagos = db.pagos_pendientes()
    if not pagos:
        console.print("  [green]✓ Sin pagos pendientes.[/green]")
    else:
        t = Table(box=box.ROUNDED)
        t.add_column("ID",     width=5)
        t.add_column("Monto",  width=10, justify="right")
        t.add_column("Método", width=15)
        t.add_column("Fecha",  width=19)
        t.add_column("Notas",  width=25)
        for p in pagos:
            t.add_row(str(p["id"]), f"${p['monto']:.2f}",
                      p["metodo"], p["fecha"], p.get("notas",""))
        console.print(t)
    input("\n  Enter para continuar...")


def main():
    db.init_db()
    while True:
        limpiar()
        console.print(Panel(
            "[bold white]REPUESTOS MADRIZ C.A.[/bold white]\n[dim]Bot MercadoLibre[/dim]",
            box=box.DOUBLE_EDGE, style="yellow"
        ))
        console.print("  [bold]1.[/bold] Ver publicaciones")
        console.print("  [bold]2.[/bold] Nueva publicación")
        console.print("  [bold]3.[/bold] Verificar pago por foto")
        console.print("  [bold]4.[/bold] Pagos pendientes")
        console.print("  [bold]5.[/bold] Decodificar VIN")
        console.print("  [bold]0.[/bold] Salir\n")

        op = input("  Opción: ").strip()
        if   op == "1": menu_publicaciones()
        elif op == "2": menu_nueva_publicacion()
        elif op == "3": menu_verificar_pago()
        elif op == "4": menu_pagos_pendientes()
        elif op == "5": menu_decodificar_vin()
        elif op == "0":
            console.print("\n  [dim]Hasta luego.[/dim]\n")
            break


if __name__ == "__main__":
    main()
