import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

spec = importlib.util.spec_from_file_location('bot', Path(__file__).with_name('bot.py'))
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)

class BotTest(unittest.TestCase):
    def setUp(self):
        self.bot = bot.Bot('123456:ABCDEFGHIJKLMNOPQRSTUVWXYZ012345', '@FreeShareMM')

    def test_join_prompt_and_gate(self):
        calls = []
        self.bot.call = lambda method, **data: calls.append((method, data)) if method == 'sendMessage' else {'status': 'left'}
        self.bot.process({'message': {'text': '/start', 'chat': {'id': 99}, 'from': {'id': 1}}})
        self.assertEqual(calls[0][1]['chat_id'], 99)
        self.assertIn('Join Channel', calls[0][1]['reply_markup'])

    def test_api_payload_and_error(self):
        with patch.object(bot.requests, 'post') as post:
            post.return_value = Mock(ok=True, json=lambda: {'ok': True, 'note': {'media': [{'absolutePath': '/tmp/test.mp4'}]}})
            self.assertEqual(len(self.bot.resolve_download('https://xhslink.com/o/123')), 1)
            self.assertEqual(post.call_args.kwargs['json']['download'], True)
        with patch.object(bot.requests, 'post') as post:
            post.return_value = Mock(ok=False, json=lambda: {'ok': False, 'error': 'Unsupported host'})
            with self.assertRaisesRegex(RuntimeError, 'Unsupported host'):
                self.bot.resolve_download('https://xhslink.com/o/123')

    def test_local_file_upload_guard(self):
        with self.assertRaisesRegex(RuntimeError, 'not found'):
            self.bot.upload_file(1, {'absolutePath': '/etc/passwd'})

    def test_download_directory_is_relative_to_bot_location(self):
        expected = Path(bot.__file__).resolve().parent / 'rednote-downloader' / 'data'
        with self.assertRaisesRegex(RuntimeError, 'not found'):
            self.bot.upload_file(1, {'absolutePath': str(expected / 'missing.mp4')})

    def test_upload_retries_connect_error_and_reopens_stream(self):
        base = Path(bot.__file__).resolve().parent / 'rednote-downloader' / 'data'
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as temp:
            file_path = Path(temp) / 'clip.mp4'
            file_path.write_bytes(b'video-content')
            seen = []
            def send(token, method, *, data=None, files=None, timeout=None):
                seen.append(files['document'][1].read())
                if len(seen) == 1:
                    raise RuntimeError('Telegram sendDocument request failed (ConnectionError)')
                return {'message_id': 123}
            with patch.object(bot, 'telegram_request', side_effect=send), patch.object(bot.time, 'sleep'):
                self.assertEqual(self.bot.upload_file(99, {'absolutePath': str(file_path)}), {'message_id': 123})
            self.assertEqual(seen, [b'video-content', b'video-content'])

    def test_upload_does_not_retry_ambiguous_timeout(self):
        base = Path(bot.__file__).resolve().parent / 'rednote-downloader' / 'data'
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as temp:
            file_path = Path(temp) / 'clip.mp4'
            file_path.write_bytes(b'video-content')
            with patch.object(bot, 'telegram_request', side_effect=RuntimeError('Telegram sendDocument request failed (ReadTimeout)')) as request:
                with self.assertRaisesRegex(RuntimeError, 'ReadTimeout'):
                    self.bot.upload_file(99, {'absolutePath': str(file_path)})
                self.assertEqual(request.call_count, 1)

    def test_token_validation(self):
        with self.assertRaises(ValueError):
            bot.Bot('\x1b[200~123:secret', '@FreeShareMM')

if __name__ == '__main__':
    unittest.main()
