# Persona Analysis — Writing Style Fingerprint

You are a communication style analyst. Given a corpus of email samples written by one person, extract a detailed writing style fingerprint.

## Corpus

{corpus}

## Instructions

Analyze the writing samples above and produce a JSON profile capturing the author's unique communication style. Look for:

1. **Overall tone** (e.g., formal, casual, warm, direct, diplomatic)
2. **Formality level** (1-5 scale, 1=very casual, 5=very formal)
3. **Vocabulary patterns** — preferred words, industry jargon, unique phrases
4. **Greeting patterns** — how they typically open emails
5. **Sign-off patterns** — how they typically close emails
6. **Sentence structure** — short/punchy vs. long/detailed, use of bullet points, etc.
7. **Response length tendency** — brief, moderate, or detailed
8. **Common phrases** — recurring expressions or idioms
9. **Things they avoid** — words, phrases, or styles they never use
10. **Email categories** — types of emails they commonly send (e.g., meeting confirmations, project updates, client outreach)

## Output Format

Respond with valid JSON only, no markdown fencing:

{
  "tone": "description of overall tone",
  "formality_level": 3,
  "vocabulary_patterns": ["word1", "word2", "phrase1"],
  "greeting_patterns": ["Hi [Name],", "Hey team,"],
  "sign_off_patterns": ["Best,", "Thanks,"],
  "sentence_structure": "description of typical sentence style",
  "response_length_tendency": "brief|moderate|detailed",
  "common_phrases": ["phrase1", "phrase2"],
  "avoids": ["things they never say or do"],
  "email_categories": ["meeting confirmations", "project updates"]
}
