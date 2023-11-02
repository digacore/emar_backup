import io
import xlsxwriter
from datetime import datetime

from app import models as m
from app.logger import logger


def create_company_billing_report(company: m.Company, from_date: datetime, to_date: datetime) -> io.BytesIO:
    """
    Generate a billing report for a company in .xlsx format and return it as BytesIO object

    Args:
        company (m.Company): company to generate the report for
        from_date (datetime): the start date of the report (EST)
        to_date (datetime): the end date of the report (EST)
    """
    output = io.BytesIO()

    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet(f'Report_{company.name}')

    # Cells styles
    bold_centered_format = workbook.add_format({'align': 'center', 'bold': True, 'border': 1})
    centered_format = workbook.add_format({'align': 'center', 'border': 1})

    # Set width of first 4 columns to 20 characters
    worksheet.set_column(0, 3, 20)

    # Merge the first 4 cells for the title
    worksheet.merge_range(0, 0, 0, 3, f"Billing Report {company.name} {from_date.strftime('%Y-%m-%d %H:%M:%S')} - {to_date.strftime('%Y-%m-%d %H:%M:%S')}", bold_centered_format)

    # Write summarized information on the top(total locations, computers, users, alerts)
    worksheet.write(1, 0, f'Total locations: {len(company.locations)}', centered_format)
    worksheet.write(1, 1, f'Total computers: {len(company.computers)}', centered_format)
    worksheet.write(1, 2, f'Total users: {len(company.users)}', centered_format)
    worksheet.write(1, 3, f'Total alerts: {company.total_alert_events(from_date, to_date, True)}', centered_format)

    # Write main table headers
    worksheet.write(3, 0, 'Location', bold_centered_format)
    worksheet.write(3, 1, 'Computer', bold_centered_format)
    worksheet.write(3, 2, 'API Calls', bold_centered_format)
    worksheet.write(3, 3, 'Alerts', bold_centered_format)

    # Write main table data
    start_row = 4
    ordered_locations = m.Location.query.filter_by(company_id=company.id).order_by(m.Location.name).all()
    for location in ordered_locations:
        worksheet.write(start_row, 0, location.name, centered_format)
        worksheet.write(start_row, 1, f'Total_computers: {location.total_computers}', centered_format)
        worksheet.write(start_row, 2, location.total_pcc_api_calls(from_date, to_date, True), centered_format)
        worksheet.write(start_row, 3, location.total_alert_events(from_date, to_date, True), centered_format)

        start_row += 1

        ordered_computers = m.Computer.query.filter_by(location_id=location.id).order_by(m.Computer.computer_name).all()

        for computer in ordered_computers:
            worksheet.write(start_row, 0, '', centered_format)
            worksheet.write(start_row, 1, computer.computer_name, centered_format)
            worksheet.write(start_row, 2, computer.total_pcc_api_calls(from_date, to_date, True), centered_format)
            worksheet.write(start_row, 3, '', centered_format)

            start_row += 1

    workbook.close()

    output.seek(0)

    logger.info(f'Created billing report for {company.name}')

    return output
