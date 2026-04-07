# Tests fuer den E-Mail-Dienst (smtplib wird gemockt)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
import email_service


def test_sende_rechnung_baut_korrekte_mail():
    """Prüft dass die E-Mail korrekt aufgebaut und abgeschickt wird"""
    fake_pdf = b"%PDF-1.4 fake content"

    with patch("smtplib.SMTP_SSL") as mock_smtp_klasse:
        mock_smtp = MagicMock()
        mock_smtp_klasse.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_klasse.return_value.__exit__ = MagicMock(return_value=False)

        email_service.sende_rechnung(
            pdf_bytes=fake_pdf,
            rechnungsnummer="RE-2026-009",
            empfaenger_name="Test GmbH",
            gmail_absender="test@gmail.com",
            gmail_passwort="geheim",
        )

        assert mock_smtp.sendmail.called
        args = mock_smtp.sendmail.call_args
        absender = args[0][0]
        empfaenger = args[0][1]
        assert absender == "test@gmail.com"
        assert empfaenger == "umohr@balance-sonnenstudio.de"
