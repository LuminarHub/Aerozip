import pandas as pd
from django.core.management.base import BaseCommand
from main.models import InternationalAirports, DomesticAirports

class Command(BaseCommand):
    help = "Upload airport data from an Excel file"

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help="Path to the Excel file")
        parser.add_argument('category', type=str, choices=['international', 'domestic'], help="Specify 'international' or 'domestic'")

    def handle(self, *args, **kwargs):
        file_path = kwargs['file']
        category = kwargs['category']

        try:
            df = pd.read_excel(file_path)
            required_columns = {"Airport Name", "IATA Code", "Location"}

            if not required_columns.issubset(df.columns):
                self.stdout.write(self.style.ERROR("Invalid file format. Required columns: Airport Name, IATA Code, Location"))
                return

            if category == "international":
                airports = [
                    InternationalAirports(
                        name=row["Airport Name"],
                        code=row["IATA Code"],
                        location=row["Location"]
                    ) for _, row in df.iterrows()
                ]
                InternationalAirports.objects.bulk_create(airports)
                self.stdout.write(self.style.SUCCESS("Successfully uploaded international airports."))

            elif category == "domestic":
                airports = [
                    DomesticAirports(
                        name=row["Airport Name"],
                        code=row["IATA Code"],
                        location=row["Location"]
                    ) for _, row in df.iterrows()
                ]
                DomesticAirports.objects.bulk_create(airports)
                self.stdout.write(self.style.SUCCESS("Successfully uploaded domestic airports."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
