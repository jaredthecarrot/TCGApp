# Implementation borrowed from open-source license provided by Nigma Software
# URL is https://www.youtube.com/watch?v=7wyvV5R_M5I&t=20s

import csv
from django.core.management.base import BaseCommand
from Main.forms import CardForm

class Command(BaseCommand):
    help = ("Imports cards from a CSV file.")
    
    def add_arguments(self, parser):
        parser.add_argument('file_path', nargs=1, type=str)

    def handle(self, *args, **options):
        self.file_path = options["file_path"][0]
        self.prepare()
        self.main()
        self.finalise()

    def prepare(self):
        self.imported_counter = 0
        self.skipped_counter = 0

    def main(self):
        self.stdout.write('=== Importing Cards === ')

        with open(self.file_path, "r") as f:
            reader = csv.DictReader(f)
            for index, row_dict in enumerate(reader):
                form = CardForm(data=row_dict)
                if form.is_valid():
                    form.save()
                    self.imported_counter += 1
                else:
                    self.stderr.write(f"Errors importing cards"
                                      f"{row_dict['productId']} - {row_dict['extNumber']}:\n"
                                      )
                    self.stderr.write(f"{form.errors.as_json()}\n")
                    self.skipped_counter += 1

    def finalise(self):
        self.stdout.write(f"----------\n")
        self.stdout.write(f"Cards Imported: {self.imported_counter}\n")
        self.stdout.write(f"Cards Skipped: {self.skipped_counter}\n\n")