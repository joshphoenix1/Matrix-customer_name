"""
Persona engine — ingest communications, build style profile,
generate reply drafts with RAG, confidence-based auto-send.
"""

import json
import os
import re
import hashlib
from datetime import datetime
from config import PROMPTS_DIR, ANTHROPIC_API_KEY, ANTHROPIC_MODEL
import db
from services import vector_store


# ── Helpers ──

def _load_prompt(filename):
    path = os.path.join(PROMPTS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return ""


def _get_claude_client():
    from anthropic import Anthropic
    api_key = db.get_setting("anthropic_api_key") or ANTHROPIC_API_KEY
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def _chunk_text(text, max_chars=500):
    """Split text into chunks of roughly max_chars at paragraph boundaries."""
    paragraphs = re.split(r"\n\s*\n", text.strip())
    chunks = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current = current + "\n\n" + para if current else para
    if current.strip():
        chunks.append(current.strip())
    return chunks if chunks else [text.strip()] if text.strip() else []


def _extract_sender_email(sender_str):
    """Extract bare email from 'Name <email@domain>' format."""
    match = re.search(r"<([^>]+)>", sender_str)
    if match:
        return match.group(1).lower()
    return sender_str.strip().lower()


# ── Ingestion ──

def ingest_emails():
    """Ingest sent emails from the database as persona training data.
    Filters to emails sent by the user (matching imap_email setting).
    """
    user_email = db.get_setting("imap_email", "")
    if not user_email:
        return {"ingested": 0, "error": "No IMAP email configured"}

    user_email_lower = user_email.lower()
    all_emails = db.get_emails(limit=500)

    # Filter to emails FROM the user (sent emails)
    sent_emails = [
        e for e in all_emails
        if user_email_lower in _extract_sender_email(e.get("sender", ""))
    ]

    # Also include all emails for context (replies the user might draft to)
    # But only store sent emails as persona samples
    existing_samples = db.get_persona_samples(source_type="email", limit=5000)
    existing_hashes = set()
    for s in existing_samples:
        meta = json.loads(s.get("metadata", "{}"))
        if meta.get("content_hash"):
            existing_hashes.add(meta["content_hash"])

    ingested = 0
    for email_data in sent_emails:
        body = email_data.get("body", "").strip()
        if not body or len(body) < 20:
            continue

        content_hash = hashlib.md5(body.encode()).hexdigest()
        if content_hash in existing_hashes:
            continue

        chunks = _chunk_text(body)
        for chunk in chunks:
            if len(chunk) < 20:
                continue
            metadata = json.dumps({
                "email_id": email_data.get("id"),
                "subject": email_data.get("subject", ""),
                "sender": email_data.get("sender", ""),
                "content_hash": content_hash,
            })
            db.save_persona_sample(chunk, source_type="email", metadata=metadata)
            ingested += 1

    return {"ingested": ingested}


def ingest_documents():
    """Ingest uploaded documents as persona training data."""
    documents = db.get_documents()
    ingested = 0

    for doc in documents:
        filepath = doc.get("filepath", "")
        if not os.path.exists(filepath):
            continue

        try:
            if doc.get("file_type", "").lower() == "pdf":
                import fitz
                pdf_doc = fitz.open(filepath)
                text = "\n".join(page.get_text() for page in pdf_doc)
                pdf_doc.close()
            else:
                with open(filepath, "r", errors="replace") as f:
                    text = f.read()
        except Exception:
            continue

        if not text.strip() or len(text) < 20:
            continue

        chunks = _chunk_text(text, max_chars=600)
        for chunk in chunks:
            if len(chunk) < 20:
                continue
            metadata = json.dumps({
                "doc_id": doc.get("id"),
                "filename": doc.get("filename", ""),
            })
            db.save_persona_sample(chunk, source_type="document", metadata=metadata)
            ingested += 1

    return {"ingested": ingested}


def ingest_chat_export(text):
    """Ingest pasted chat/text export as persona training data."""
    if not text or len(text.strip()) < 20:
        return {"ingested": 0}

    chunks = _chunk_text(text, max_chars=500)
    ingested = 0
    for chunk in chunks:
        if len(chunk) < 20:
            continue
        metadata = json.dumps({"source": "chat_export"})
        db.save_persona_sample(chunk, source_type="chat", metadata=metadata)
        ingested += 1

    return {"ingested": ingested}


# ── Embedding ──

def embed_pending_samples():
    """Embed all unembedded persona samples into ChromaDB."""
    samples = db.get_unembedded_samples()
    if not samples:
        return {"embedded": 0}

    ids = [f"sample_{s['id']}" for s in samples]
    documents = [s["content"] for s in samples]
    metadatas = []
    for s in samples:
        meta = json.loads(s.get("metadata", "{}"))
        meta["source_type"] = s["source_type"]
        # ChromaDB metadata values must be str, int, float, or bool
        metadatas.append({k: str(v) for k, v in meta.items()})

    vector_store.add_documents(ids, documents, metadatas)

    for s in samples:
        db.mark_sample_embedded(s["id"])

    return {"embedded": len(samples)}


# ── Profile Building ──

def build_persona_profile():
    """Sample emails and call Claude to extract a writing style fingerprint."""
    client = _get_claude_client()
    if not client:
        return {"error": "No API key configured"}

    samples = db.get_persona_samples(limit=500)
    if not samples:
        return {"error": "No persona samples found. Ingest emails first."}

    # Sample up to 50 diverse samples for profile building
    import random
    sample_pool = samples[:200]
    selected = random.sample(sample_pool, min(50, len(sample_pool)))

    corpus = "\n\n---\n\n".join(s["content"] for s in selected)

    prompt_template = _load_prompt("persona_analysis_prompt.md")
    if not prompt_template:
        return {"error": "Persona analysis prompt not found"}

    prompt = prompt_template.replace("{corpus}", corpus)

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Try to extract JSON from the response
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            profile = json.loads(json_match.group())
        else:
            profile = {"raw_analysis": raw}

        db.save_setting("persona_profile", json.dumps(profile))
        return {"success": True, "profile": profile}
    except Exception as e:
        return {"error": str(e)}


# ── Draft Generation ──

def generate_reply_draft(incoming_email_id):
    """RAG pipeline: query similar past responses → load persona profile →
    call Claude → score confidence → save draft."""
    client = _get_claude_client()
    if not client:
        return None

    # Load the incoming email
    emails = db.get_emails(limit=500)
    email_data = next((e for e in emails if e["id"] == incoming_email_id), None)
    if not email_data:
        return None

    # Check if draft already exists for this email
    existing_drafts = db.get_email_drafts(limit=500)
    if any(d.get("email_id") == incoming_email_id for d in existing_drafts):
        return None

    sender = email_data.get("sender", "")
    subject = email_data.get("subject", "")
    body = email_data.get("body", "")

    # Load persona profile
    profile_json = db.get_setting("persona_profile")
    if not profile_json:
        return None
    try:
        persona_profile = json.loads(profile_json)
    except Exception:
        return None

    # RAG: query similar communications
    query_text = f"{subject} {body[:500]}"
    similar = vector_store.query(query_text, n_results=5)

    similar_examples = ""
    if similar.get("documents") and similar["documents"][0]:
        examples = similar["documents"][0]
        similar_examples = "\n\n---\n\n".join(examples)

    # Load and fill prompt template
    prompt_template = _load_prompt("persona_reply_prompt.md")
    if not prompt_template:
        return None

    prompt = prompt_template.replace("{persona_profile}", json.dumps(persona_profile, indent=2))
    prompt = prompt.replace("{similar_examples}", similar_examples or "No similar examples found.")
    prompt = prompt.replace("{sender}", sender)
    prompt = prompt.replace("{subject}", subject)
    prompt = prompt.replace("{body}", body[:3000])

    try:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()

        # Parse JSON response
        json_match = re.search(r"\{[\s\S]*\}", raw)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {"reply_body": raw, "category": "general", "reasoning": "Could not parse structured response"}

        reply_body = result.get("reply_body", "")
        category = result.get("category", "general")
        reasoning = result.get("reasoning", "")

        if not reply_body:
            return None

        # Score confidence
        confidence = _score_confidence(
            email_data, reply_body, category, similar, sender
        )

        # Determine status based on confidence and auto-reply setting
        auto_reply_enabled = db.get_setting("persona_auto_reply_enabled", "false") == "true"
        threshold = float(db.get_setting("persona_confidence_threshold", "0.85"))

        if auto_reply_enabled and confidence >= threshold:
            status = "auto_approved"
        else:
            status = "pending_review"

        # Save draft
        draft_id = db.save_email_draft(
            email_id=incoming_email_id,
            recipient=sender,
            subject=f"Re: {subject}" if not subject.startswith("Re:") else subject,
            body=reply_body,
            status=status,
            confidence_score=confidence,
            category=category,
            reasoning=reasoning,
            original_body=body[:5000],
        )

        return draft_id

    except Exception as e:
        print(f"Error generating draft for email {incoming_email_id}: {e}")
        return None


def _score_confidence(email_data, reply_body, category, similar_results, sender):
    """Rule-based confidence scoring. Returns float 0.0-1.0."""
    score = 0.5  # Base score

    subject = email_data.get("subject", "").lower()
    body = email_data.get("body", "").lower()
    urgency = email_data.get("urgency", "routine")

    # +0.3 for routine acknowledgments / meeting confirmations
    ack_patterns = [
        "confirm", "acknowledge", "received", "got it", "thank",
        "meeting confirm", "calendar invite", "rsvp", "accepted",
    ]
    if any(pat in subject or pat in body for pat in ack_patterns):
        score += 0.3

    # +0.1 for high similarity to past responses
    if similar_results.get("distances") and similar_results["distances"][0]:
        best_distance = min(similar_results["distances"][0])
        if best_distance < 0.3:
            score += 0.1

    # -0.3 for numbers, dollar amounts, commitments
    commitment_patterns = [
        r"\$\d+", r"\d+%", "deadline", "commit", "promise", "guarantee",
        "contract", "agreement", "budget", "invoice", "payment",
    ]
    for pat in commitment_patterns:
        if re.search(pat, body) or re.search(pat, subject):
            score -= 0.3
            break

    # -0.2 for unknown/new sender
    all_emails = db.get_emails(limit=200)
    known_senders = {e.get("sender", "").lower() for e in all_emails}
    sender_lower = sender.lower()
    sender_seen = any(sender_lower in s for s in known_senders)
    if not sender_seen:
        score -= 0.2

    # -0.3 for critical/important urgency
    if urgency in ("critical", "important"):
        score -= 0.3

    # Clamp to 0.0-1.0
    return max(0.0, min(1.0, round(score, 2)))


# ── Batch Processing ──

def process_new_emails_for_drafts():
    """Generate drafts for all unprocessed emails."""
    profile_json = db.get_setting("persona_profile")
    if not profile_json:
        return {"processed": 0, "error": "No persona profile. Build profile first."}

    all_emails = db.get_emails(limit=100)
    existing_drafts = db.get_email_drafts(limit=500)
    drafted_email_ids = {d.get("email_id") for d in existing_drafts}

    user_email = db.get_setting("imap_email", "").lower()
    processed = 0

    for email_data in all_emails:
        if email_data["id"] in drafted_email_ids:
            continue
        # Skip emails from the user themselves
        sender = _extract_sender_email(email_data.get("sender", ""))
        if user_email and user_email in sender:
            continue

        draft_id = generate_reply_draft(email_data["id"])
        if draft_id:
            processed += 1

    return {"processed": processed}


# ── Rebuild ──

def rebuild_persona():
    """Full rebuild: clear ChromaDB, re-ingest all, rebuild profile."""
    vector_store.delete_collection()
    db.clear_persona_samples()

    ingest_result = ingest_emails()
    embed_result = embed_pending_samples()
    profile_result = build_persona_profile()

    return {
        "ingested": ingest_result.get("ingested", 0),
        "embedded": embed_result.get("embedded", 0),
        "profile": profile_result,
    }
