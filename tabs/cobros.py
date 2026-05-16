"""Tab Cobros pendientes."""
from tabs._deuda import render_deuda


def render(ctx: dict) -> None:
    render_deuda(ctx, "cobros")
