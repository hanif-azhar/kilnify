"""Report generation, detail, CSV/PDF export, and deletion."""
import csv
import io
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Company, EmissionEntry, ProductionData, Report
from ..schemas import ReportGenerate, ReportOut
from ..services import aggregator

router = APIRouter(prefix="/api/reports", tags=["reports"])

DISCLAIMER = (
    "This report is generated based on user-provided activity data and industry-standard "
    "emission factors. It has not been independently verified and should not be used for "
    "regulatory reporting without review by a certified carbon accountant or third-party verifier."
)

METHODOLOGY_NOTES = [
    "Calculations follow: Emissions (kgCO2e) = Activity Data x Emission Factor.",
    "Clinker process emissions use Method A (clinker x default EF 525 kgCO2/t, WBCSD CSI/GNR) "
    "or Method B (CaO/MgO stoichiometry, IPCC 2006) where plant-specific data exists.",
    "Scope 2 uses the location-based Indonesian PLN regional grid factor by default.",
    "GWP values per IPCC AR6 (2021), GWP-100.",
    "Biogenic CO2 from alternative fuels is excluded from the inventory total and disclosed separately.",
    "Scope 3 is classified by GHG Protocol Corporate Value Chain category (1-15).",
    "Thermal Substitution Rate (TSR) is energy-based: alternative-fuel GJ / total kiln-fuel GJ.",
    "Standards: GHG Protocol Corporate Standard, WBCSD CSI / GCCA Cement CO2 Protocol.",
]


def _entries_for_period(db: Session, company_id: str, start, end) -> List[EmissionEntry]:
    return (
        db.query(EmissionEntry)
        .filter(
            EmissionEntry.company_id == company_id,
            EmissionEntry.period_start >= start,
            EmissionEntry.period_end <= end,
        )
        .all()
    )


def _production_for_period(db: Session, company_id: str, start, end) -> List[ProductionData]:
    return (
        db.query(ProductionData)
        .filter(
            ProductionData.company_id == company_id,
            ProductionData.period_start >= start,
            ProductionData.period_end <= end,
        )
        .all()
    )


@router.get("/", response_model=list[ReportOut])
def list_reports(company_id: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(Report)
    if company_id:
        q = q.filter(Report.company_id == company_id)
    return q.order_by(Report.generated_at.desc()).all()


@router.post("/generate", response_model=ReportOut, status_code=201)
def generate_report(payload: ReportGenerate, db: Session = Depends(get_db)):
    company = db.get(Company, payload.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    entries = _entries_for_period(db, payload.company_id, payload.period_start, payload.period_end)
    production = _production_for_period(db, payload.company_id, payload.period_start, payload.period_end)

    breakdown = aggregator.scope_breakdown(entries)
    intensity = aggregator.intensity_metrics(entries, production)

    report = Report(
        company_id=payload.company_id,
        report_period=payload.report_period,
        period_start=payload.period_start,
        period_end=payload.period_end,
        total_scope1_process=round(breakdown["scope1_process_tco2e"], 4),
        total_scope1_combustion=round(breakdown["scope1_combustion_tco2e"], 4),
        total_scope1_mobile=round(breakdown["scope1_mobile_tco2e"], 4),
        total_scope1_fugitive=round(breakdown["scope1_fugitive_tco2e"], 4),
        total_scope1=round(breakdown["scope1_tco2e"], 4),
        # Default Scope 2 to location-based; market-based mirrors it unless overridden.
        total_scope2_lb=round(breakdown["scope2_tco2e"], 4),
        total_scope2_mb=round(breakdown["scope2_tco2e"], 4),
        total_scope3=round(breakdown["scope3_tco2e"], 4),
        total_emissions=round(breakdown["total_tco2e"], 4),
        biogenic_co2_total=round(breakdown["biogenic_co2_tco2e"], 4),
        specific_emissions_per_tonne_cement=intensity["intensity_kgco2e_per_tonne_cement"],
        specific_emissions_per_tonne_clinker=intensity["intensity_kgco2e_per_tonne_clinker"],
        clinker_to_cement_ratio=intensity["clinker_to_cement_ratio"],
        unit="tCO2e",
        status=payload.status,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/detail")
def report_detail(report_id: str, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    company = db.get(Company, report.company_id)
    entries = _entries_for_period(db, report.company_id, report.period_start, report.period_end)

    base = ReportOut.model_validate(report).model_dump(mode="json")
    base.update(
        {
            "company_name": company.name if company else "Unknown",
            "facility_type": company.facility_type if company else "unknown",
            "entries": [
                {
                    "id": e.id,
                    "scope": e.scope,
                    "category": e.category,
                    "sub_category": e.sub_category,
                    "activity_data": e.activity_data,
                    "activity_unit": e.activity_unit,
                    "emission_factor": e.emission_factor,
                    "emission_factor_unit": e.emission_factor_unit,
                    "emission_factor_source": e.emission_factor_source,
                    "total_emissions_kgco2e": e.total_emissions_kgco2e,
                    "biogenic_co2_kgco2": e.biogenic_co2_kgco2,
                    "data_quality": e.data_quality,
                    "calculation_method": e.calculation_method,
                    "plant_area": e.plant_area,
                }
                for e in entries
            ],
            "top_hotspots": aggregator.top_hotspots(entries),
            "scope2_by_category": aggregator.emissions_by_category(entries, "2"),
            "scope3_by_category": aggregator.scope3_category_breakdown(entries),
            "alternative_fuel_metrics": aggregator.alternative_fuel_metrics(entries),
            "data_quality_summary": aggregator.data_quality_summary(entries),
            "methodology_notes": METHODOLOGY_NOTES,
            "disclaimer": DISCLAIMER,
        }
    )
    return base


@router.get("/{report_id}/export/csv")
def export_csv(report_id: str, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    entries = _entries_for_period(db, report.company_id, report.period_start, report.period_end)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "scope", "category", "sub_category", "activity_data", "activity_unit",
            "emission_factor", "emission_factor_unit", "emission_factor_source",
            "total_emissions_kgco2e", "total_emissions_tco2e", "biogenic_co2_kgco2",
            "data_quality", "calculation_method", "plant_area", "period_start", "period_end",
        ]
    )
    for e in entries:
        writer.writerow(
            [
                e.scope, e.category, e.sub_category or "", e.activity_data, e.activity_unit,
                e.emission_factor, e.emission_factor_unit or "", e.emission_factor_source,
                e.total_emissions_kgco2e, round(e.total_emissions_kgco2e / 1000.0, 4),
                e.biogenic_co2_kgco2 or 0.0, e.data_quality, e.calculation_method or "",
                e.plant_area or "", e.period_start, e.period_end,
            ]
        )
    buf.seek(0)
    filename = f"kilnify_report_{report_id}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{report_id}/export/pdf")
def export_pdf(report_id: str, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    company = db.get(Company, report.company_id)
    entries = _entries_for_period(db, report.company_id, report.period_start, report.period_end)
    hotspots = aggregator.top_hotspots(entries)

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
        )
    except ImportError:
        raise HTTPException(status_code=501, detail="PDF export requires reportlab. pip install reportlab.")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title=f"Kilnify Report — {report.report_period}")
    styles = getSampleStyleSheet()
    story = []

    # Cover
    story.append(Paragraph("Kilnify Carbon Footprint Report", styles["Title"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"<b>Facility:</b> {company.name if company else 'Unknown'}", styles["Normal"]))
    story.append(Paragraph(f"<b>Facility type:</b> {company.facility_type if company else 'unknown'}", styles["Normal"]))
    story.append(Paragraph(f"<b>Reporting period:</b> {report.report_period} ({report.period_start} to {report.period_end})", styles["Normal"]))
    story.append(Paragraph(f"<b>Status:</b> {report.status}", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    # Executive summary
    story.append(Paragraph("Executive Summary", styles["Heading2"]))
    story.append(Paragraph(f"Total emissions: <b>{report.total_emissions:,.2f} tCO2e</b>", styles["Normal"]))
    if report.specific_emissions_per_tonne_cement is not None:
        story.append(Paragraph(f"Specific emissions: {report.specific_emissions_per_tonne_cement:,.2f} kgCO2e/t cement", styles["Normal"]))
    if report.clinker_to_cement_ratio is not None:
        story.append(Paragraph(f"Clinker-to-cement ratio: {report.clinker_to_cement_ratio:.2%}", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    # Scope breakdown table
    story.append(Paragraph("Scope Breakdown (tCO2e)", styles["Heading2"]))
    scope_table = Table(
        [
            ["Scope", "tCO2e"],
            ["Scope 1 — Process", f"{report.total_scope1_process:,.2f}"],
            ["Scope 1 — Combustion", f"{report.total_scope1_combustion:,.2f}"],
            ["Scope 1 — Mobile", f"{report.total_scope1_mobile:,.2f}"],
            ["Scope 1 — Fugitive", f"{report.total_scope1_fugitive:,.2f}"],
            ["Scope 1 — Total", f"{report.total_scope1:,.2f}"],
            ["Scope 2 (location-based)", f"{report.total_scope2_lb:,.2f}"],
            ["Scope 3", f"{report.total_scope3:,.2f}"],
            ["TOTAL", f"{report.total_emissions:,.2f}"],
        ]
    )
    scope_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f6feb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ]
        )
    )
    story.append(scope_table)
    story.append(Spacer(1, 0.4 * cm))

    # Hotspots
    if hotspots:
        story.append(Paragraph("Top 5 Emission Hotspots", styles["Heading2"]))
        rows = [["Category", "tCO2e", "%"]] + [
            [h["category"], f"{h['emissions_tco2e']:,.2f}", f"{h['percentage']:.1f}%"] for h in hotspots
        ]
        ht = Table(rows)
        ht.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaeef2"))]))
        story.append(ht)
        story.append(Spacer(1, 0.4 * cm))

    # Biogenic disclosure
    story.append(Paragraph("Biogenic CO2 Disclosure", styles["Heading2"]))
    story.append(Paragraph(
        f"Biogenic CO2 (excluded from inventory total, disclosed separately): "
        f"{report.biogenic_co2_total:,.2f} tCO2", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))

    # Methodology + disclaimer
    story.append(Paragraph("Methodology Notes", styles["Heading2"]))
    for note in METHODOLOGY_NOTES:
        story.append(Paragraph(f"• {note}", styles["Normal"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Disclaimer", styles["Heading2"]))
    story.append(Paragraph(DISCLAIMER, styles["Italic"]))

    doc.build(story)
    buf.seek(0)
    filename = f"kilnify_report_{report_id}.pdf"
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: str, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
