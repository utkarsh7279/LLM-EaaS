"""Export functionality for experiments and results in multiple formats."""

import csv
import io
import json
from datetime import datetime
from typing import Any
from uuid import UUID

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch

    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class ExperimentExporter:
    """Export experiment results in multiple formats."""

    @staticmethod
    def to_json(experiment_data: dict[str, Any], results: list[dict[str, Any]]) -> str:
        """Export to JSON format."""

        def json_serializer(obj: Any) -> str:
            """Handle non-serializable types."""
            if isinstance(obj, UUID):
                return str(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        export_data = {
            "experiment": experiment_data,
            "results": results,
            "exported_at": datetime.utcnow().isoformat(),
            "format_version": "1.0",
        }

        return json.dumps(export_data, indent=2, default=json_serializer)

    @staticmethod
    def to_csv(
        experiment_data: dict[str, Any],
        results: list[dict[str, Any]],
        include_metadata: bool = True,
    ) -> str:
        """Export to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)

        if include_metadata:
            # Metadata section
            writer.writerow(["EXPERIMENT METADATA"])
            writer.writerow(["Field", "Value"])
            for key, value in experiment_data.items():
                if not isinstance(value, (list, dict)):
                    writer.writerow([key, value])
            writer.writerow([])
            writer.writerow([])

        # Results section
        if results:
            writer.writerow(["EVALUATION RESULTS"])
            fieldnames = results[0].keys()
            writer.writerow(fieldnames)

            for result in results:
                row = []
                for field in fieldnames:
                    value = result.get(field, "")
                    # Handle nested structures
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    row.append(str(value))
                writer.writerow(row)

        return output.getvalue()

    @staticmethod
    def to_pdf(
        experiment_data: dict[str, Any],
        results: list[dict[str, Any]],
        filename: str = "experiment_results.pdf",
    ) -> bytes:
        """Export to PDF format.

        Requires reportlab: pip install reportlab
        """
        if not HAS_REPORTLAB:
            raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=0.5 * inch, bottomMargin=0.5 * inch)
        story = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=30,
            alignment=1,  # Center
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#374151"),
            spaceAfter=12,
            spaceBefore=12,
        )

        # Title
        story.append(Paragraph("Experiment Results Report", title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Metadata section
        story.append(Paragraph("Experiment Metadata", heading_style))
        metadata_table_data = [["Field", "Value"]]
        for key, value in experiment_data.items():
            if not isinstance(value, (list, dict)):
                metadata_table_data.append([str(key), str(value)])

        metadata_table = Table(metadata_table_data, colWidths=[2.5 * inch, 5 * inch])
        metadata_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                ]
            )
        )
        story.append(metadata_table)
        story.append(Spacer(1, 0.3 * inch))

        # Results section
        if results:
            story.append(PageBreak())
            story.append(Paragraph("Evaluation Results", heading_style))

            results_table_data = [list(results[0].keys())]
            for result in results[:50]:  # Limit to first 50 for readability
                row = []
                for value in result.values():
                    if isinstance(value, (dict, list)):
                        row.append(json.dumps(value)[:50] + "..." if len(json.dumps(value)) > 50 else json.dumps(value))
                    else:
                        row.append(str(value))
                results_table_data.append(row)

            if len(results) > 50:
                results_table_data.append([f"... and {len(results) - 50} more results"])

            results_table = Table(results_table_data)
            results_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                    ]
                )
            )
            story.append(results_table)

        # Footer
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"<i>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>", styles["Normal"]))

        # Build PDF
        doc.build(story)
        return buffer.getvalue()

    @staticmethod
    def to_html(experiment_data: dict[str, Any], results: list[dict[str, Any]]) -> str:
        """Export to HTML format."""
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="UTF-8">',
            "<title>Experiment Results</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1, h2 { color: #1f2937; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #d1d5db; padding: 12px; text-align: left; }",
            "th { background-color: #1f2937; color: white; }",
            "tr:nth-child(even) { background-color: #f3f4f6; }",
            ".metadata { background-color: #f9fafb; padding: 15px; margin: 20px 0; border-left: 4px solid #3b82f6; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Experiment Results Report</h1>",
        ]

        # Metadata
        html_parts.append("<div class='metadata'>")
        html_parts.append("<h2>Experiment Metadata</h2>")
        html_parts.append("<table>")
        html_parts.append("<tr><th>Field</th><th>Value</th></tr>")
        for key, value in experiment_data.items():
            if not isinstance(value, (list, dict)):
                html_parts.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
        html_parts.append("</table>")
        html_parts.append("</div>")

        # Results
        if results:
            html_parts.append("<h2>Evaluation Results</h2>")
            html_parts.append("<table>")
            html_parts.append("<tr>")
            for field in results[0].keys():
                html_parts.append(f"<th>{field}</th>")
            html_parts.append("</tr>")

            for result in results:
                html_parts.append("<tr>")
                for value in result.values():
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    html_parts.append(f"<td>{value}</td>")
                html_parts.append("</tr>")

            html_parts.append("</table>")

        html_parts.append(f"<p><i>Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</i></p>")
        html_parts.extend(["</body>", "</html>"])

        return "\n".join(html_parts)
