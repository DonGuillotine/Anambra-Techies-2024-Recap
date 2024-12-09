import re
from datetime import datetime
from typing import Dict, Optional, Generator
from django.db import transaction
from users.models import User
from whatsapp_messages.models import Message
import pytz

class WhatsAppMessageParser:
    def __init__(self):
        self.message_pattern = re.compile(
            r'(\d{1,2}/\d{1,2}/\d{2}),\s(\d{1,2}:\d{2})\s-\s(\+\d+\s\d+\s\d+\s\d+):\s(.*)'
        )
        self.media_indicators = [
            '<Media omitted>',
            'image omitted',
            'video omitted',
            'audio omitted',
            'document omitted'
        ]
        self.timezone = pytz.timezone('Africa/Lagos')

    def parse_timestamp(self, date_str: str, time_str: str) -> datetime:
        """Convert date and time strings to timezone-aware datetime object."""
        datetime_str = f"{date_str} {time_str}"
        naive_datetime = datetime.strptime(datetime_str, "%m/%d/%y %H:%M")
        return self.timezone.localize(naive_datetime)

    def detect_message_type(self, content: str) -> str:
        """Detect the type of message based on content."""
        content_lower = content.lower()
        if any(indicator.lower() in content_lower for indicator in self.media_indicators):
            if 'image' in content_lower:
                return 'IMAGE'
            elif 'video' in content_lower:
                return 'VIDEO'
            elif 'audio' in content_lower:
                return 'AUDIO'
            elif 'document' in content_lower:
                return 'DOCUMENT'
        return 'TEXT'

    def parse_line(self, line: str) -> Optional[Dict]:
        """Parse a single line from the chat file."""
        match = self.message_pattern.match(line.strip())
        if not match:
            return None

        date, time, phone_number, content = match.groups()
        
        try:
            timestamp = self.parse_timestamp(date, time)
            message_type = self.detect_message_type(content)
            
            return {
                'timestamp': timestamp,
                'phone_number': phone_number.strip(),
                'content': content.strip(),
                'message_type': message_type
            }
        except ValueError:
            return None

    def process_chat_file(self, file_path: str, batch_size: int = 1000) -> Generator:
        """Process the chat file in batches."""
        messages_batch = []
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                parsed_message = self.parse_line(line)
                if parsed_message:
                    messages_batch.append(parsed_message)
                    
                    if len(messages_batch) >= batch_size:
                        yield messages_batch
                        messages_batch = []
            
            if messages_batch:
                yield messages_batch

class ChatImportService:
    def __init__(self):
        self.parser = WhatsAppMessageParser()

    @transaction.atomic
    def process_messages_batch(self, messages_batch: list):
        """Process and save a batch of messages."""
        for message_data in messages_batch:
            user, _ = User.objects.get_or_create(
                phone_number=message_data['phone_number']
            )

            Message.objects.create(
                sender=user,
                content=message_data['content'],
                timestamp=message_data['timestamp'],
                message_type=message_data['message_type']
            )

    def import_chat(self, file_path: str):
        """Import the entire chat file."""
        total_messages = 0
        total_users = set()

        for batch in self.parser.process_chat_file(file_path):
            self.process_messages_batch(batch)
            total_messages += len(batch)
            total_users.update(msg['phone_number'] for msg in batch)

        return {
            'total_messages': total_messages,
            'total_users': len(total_users)
        }
