from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)

from django.utils.formats import date_format
from django.utils.timezone import now

from inflows.models import Inflow
from outflows.models import Outflow
from investments.models import InvestmentAsset
from categories.models import Category


STYLE_TITLE = ParagraphStyle(
    'CustomTitle',
    parent=getSampleStyleSheet()['Title'],
    fontSize=18,
    spaceAfter=20,
)

STYLE_SUBTITLE = ParagraphStyle(
    'CustomSubtitle',
    parent=getSampleStyleSheet()['Normal'],
    fontSize=10,
    textColor=colors.grey,
    spaceAfter=16,
)

STYLE_SECTION = ParagraphStyle(
    'SectionTitle',
    parent=getSampleStyleSheet()['Heading2'],
    fontSize=14,
    spaceBefore=16,
    spaceAfter=10,
)

TABLE_STYLE = TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4f8')]),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
])


def _fmt(value):
    return f'R$ {Decimal(value):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def _build_doc(buffer, title):
    return SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=1.5 * cm,
        title=title,
    )


def _header(story, title, username):
    story.append(Paragraph('GAW Finance', STYLE_TITLE))
    story.append(Paragraph(title, STYLE_SECTION))
    story.append(Paragraph(
        f'Usuario: {username} | Gerado em: {date_format(now(), "d/m/Y H:i")}',
        STYLE_SUBTITLE,
    ))
    story.append(Spacer(1, 0.5 * cm))


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(1.5 * cm, 1 * cm, f'GAW Finance - Pagina {doc.page}')
    canvas.drawRightString(A4[0] - 1.5 * cm, 1 * cm, date_format(now(), 'd/m/Y H:i'))
    canvas.restoreState()


def generate_cash_flow_report(user, month=None, year=None):
    buffer = BytesIO()
    doc = _build_doc(buffer, 'Fluxo de Caixa')
    story = []

    _header(story, 'Relatório de Fluxo de Caixa', user.username)

    inflows_qs = Inflow.objects.filter(user=user)
    outflows_qs = Outflow.objects.filter(user=user)

    if month and year:
        inflows_qs = inflows_qs.filter(created_at__month=month, created_at__year=year)
        outflows_qs = outflows_qs.filter(created_at__month=month, created_at__year=year)
        period_label = f'{month:02d}/{year}'
    else:
        period_label = 'Todo o período'

    story.append(Paragraph(f'Período: {period_label}', STYLE_SECTION))

    total_inflows = sum(i.value for i in inflows_qs)
    total_outflows = sum(o.value for o in outflows_qs)
    balance = total_inflows - total_outflows

    summary_data = [
        ['Métrica', 'Valor'],
        ['Total de Entradas', _fmt(total_inflows)],
        ['Total de Saídas', _fmt(total_outflows)],
        ['Saldo do Período', _fmt(balance)],
    ]
    summary_table = Table(summary_data, colWidths=[8 * cm, 8 * cm])
    summary_table.setStyle(TABLE_STYLE)
    story.append(summary_table)
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph('Entradas', STYLE_SECTION))
    inflow_data = [['Data', 'Banco', 'Valor']]
    for inflow in inflows_qs:
        inflow_data.append([
            date_format(inflow.created_at, 'd/m/Y'),
            str(inflow.bank),
            _fmt(inflow.value),
        ])
    if len(inflow_data) == 1:
        inflow_data.append(['-', 'Nenhuma entrada', '-'])
    inflow_table = Table(inflow_data, colWidths=[4 * cm, 8 * cm, 4 * cm])
    inflow_table.setStyle(TABLE_STYLE)
    story.append(inflow_table)
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph('Saídas', STYLE_SECTION))
    outflow_data = [['Data', 'Banco', 'Categoria', 'Valor']]
    for outflow in outflows_qs:
        outflow_data.append([
            date_format(outflow.created_at, 'd/m/Y'),
            str(outflow.bank),
            str(outflow.category) if outflow.category else '-',
            _fmt(outflow.value),
        ])
    if len(outflow_data) == 1:
        outflow_data.append(['-', 'Nenhuma saída', '-', '-'])
    outflow_table = Table(outflow_data, colWidths=[3.5 * cm, 5 * cm, 5 * cm, 3.5 * cm])
    outflow_table.setStyle(TABLE_STYLE)
    story.append(outflow_table)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer


def generate_expenses_by_category_report(user, month=None, year=None):
    buffer = BytesIO()
    doc = _build_doc(buffer, 'Despesas por Categoria')
    story = []

    _header(story, 'Relatório de Despesas por Categoria', user.username)

    outflows_qs = Outflow.objects.filter(user=user)
    if month and year:
        outflows_qs = outflows_qs.filter(created_at__month=month, created_at__year=year)
        period_label = f'{month:02d}/{year}'
    else:
        period_label = 'Todo o período'

    story.append(Paragraph(f'Período: {period_label}', STYLE_SECTION))

    categories = Category.objects.filter(user=user)
    cat_data = [['Categoria', 'Número de Saídas', 'Total']]
    total_all = Decimal(0)

    for cat in categories:
        cat_outflows = outflows_qs.filter(category=cat)
        total = sum(o.value for o in cat_outflows)
        count = cat_outflows.count()
        if count > 0:
            cat_data.append([cat.name, str(count), _fmt(total)])
            total_all += total

    uncategorized = outflows_qs.filter(category__isnull=True)
    if uncategorized.exists():
        total_unc = sum(o.value for o in uncategorized)
        cat_data.append(['Sem categoria', str(uncategorized.count()), _fmt(total_unc)])
        total_all += total_unc

    if len(cat_data) == 1:
        cat_data.append(['Nenhuma despesa encontrada', '-', '-'])

    cat_data.append(['TOTAL', '', _fmt(total_all)])
    cat_table = Table(cat_data, colWidths=[8 * cm, 4 * cm, 5 * cm])
    cat_table.setStyle(TABLE_STYLE)
    cat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    story.append(cat_table)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer


def generate_investments_report(user):
    buffer = BytesIO()
    doc = _build_doc(buffer, 'Investimentos')
    story = []

    _header(story, 'Relatório de Investimentos', user.username)

    assets = InvestmentAsset.objects.filter(user=user).select_related('bank')

    total_current = sum(a.current_value for a in assets)
    total_active = assets.filter(is_active=True).count()

    summary_data = [
        ['Métrica', 'Valor'],
        ['Total Investido', _fmt(total_current)],
        ['Ativos Ativos', str(total_active)],
        ['Total de Ativos', str(assets.count())],
    ]
    summary_table = Table(summary_data, colWidths=[8 * cm, 8 * cm])
    summary_table.setStyle(TABLE_STYLE)
    story.append(summary_table)
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph('Carteira de Investimentos', STYLE_SECTION))
    asset_data = [['Ativo', 'Tipo', 'Instituição', 'Valor Atual', 'Status']]

    for asset in assets:
        asset_data.append([
            asset.name,
            asset.get_asset_type_display(),
            asset.institution or '-',
            _fmt(asset.current_value),
            'Ativo' if asset.is_active else 'Inativo',
        ])

    if len(asset_data) == 1:
        asset_data.append(['Nenhum investimento encontrado', '-', '-', '-', '-'])

    asset_table = Table(asset_data, colWidths=[4 * cm, 3 * cm, 4 * cm, 3 * cm, 2.5 * cm])
    asset_table.setStyle(TABLE_STYLE)
    story.append(asset_table)

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer
