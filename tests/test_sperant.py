from magic.sperant import SperantWebhookEvent, classify_webhook


def test_sale_event_recomputes_pricing():
    event = SperantWebhookEvent(event_type="sale.completed")
    assert classify_webhook(event) == "recompute_pricing"


def test_lead_event_refreshes_demand_features():
    event = SperantWebhookEvent(event_type="lead.created")
    assert classify_webhook(event) == "refresh_demand_features"


def test_unknown_event_is_preserved_without_side_effect():
    event = SperantWebhookEvent(event_type="contact.note.created")
    assert classify_webhook(event) == "store_only"
