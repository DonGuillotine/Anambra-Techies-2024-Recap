from django.core.management.base import BaseCommand
from core.parsers.whatsapp_parser import ChatImportService

class Command(BaseCommand):
    help = 'Import WhatsApp chat file into the database'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the chat file')

    def handle(self, *args, **options):
        file_path = options['file_path']
        
        self.stdout.write(self.style.SUCCESS(f'Starting import from {file_path}'))
        
        import_service = ChatImportService()
        try:
            results = import_service.import_chat(file_path)
            
            self.stdout.write(self.style.SUCCESS(
                f"Successfully imported {results['total_messages']} messages "
                f"from {results['total_users']} users"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error during import: {str(e)}'))
