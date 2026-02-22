"""
Seed script — populates team chat channels with realistic messages.
Run once: python3 seed_chat.py
"""

import db
from datetime import datetime, timedelta

# Helper to create messages with staggered timestamps
BASE_TIME = datetime.now() - timedelta(hours=6)
msg_counter = [0]

def _msg(channel_id, sender, color, content, minutes_offset=None):
    if minutes_offset is None:
        msg_counter[0] += 3
        minutes_offset = msg_counter[0]
    ts = (BASE_TIME + timedelta(minutes=minutes_offset)).strftime("%Y-%m-%d %H:%M:%S")
    with db.get_db() as conn:
        conn.execute(
            "INSERT INTO channel_messages (channel_id, sender_name, sender_avatar_color, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (channel_id, sender, color, content, ts),
        )


PEOPLE = {
    "Alex Rivera":     "#6C5CE7",
    "Nicole Torres":   "#00B894",
    "Marcus Chen":     "#0984E3",
    "Sarah Kim":       "#E17055",
    "James Wilson":    "#FDCB6E",
    "Elena Rodriguez": "#FD79A8",
    "David Park":      "#55EFC4",
    "Maya Johnson":    "#A29BFE",
}


def main():
    print("Initializing database...")
    db.init_db()

    print("\nCreating channels...")
    ch_general = db.create_channel("general", "Company-wide announcements and discussion")
    ch_eng = db.create_channel("engineering", "Engineering team discussions, PRs, and technical decisions")
    ch_product = db.create_channel("product", "Product roadmap, feature requests, and design reviews")
    ch_random = db.create_channel("random", "Water cooler chat, memes, and off-topic fun")
    ch_sales = db.create_channel("sales", "Deal pipeline, customer feedback, and GTM strategy")
    print(f"  Created {5} channels")

    print("\nSeeding #general...")
    msg_counter[0] = 0
    _msg(ch_general, "Alex Rivera", PEOPLE["Alex Rivera"],
         "Good morning team! Quick update: we just received our 4th term sheet for the Series A. The board is meeting this afternoon to review all offers. Huge milestone for M8TRX.AI.")
    _msg(ch_general, "Maya Johnson", PEOPLE["Maya Johnson"],
         "That's incredible news! Congrats to everyone who made this happen. The traction we've built in 6 months is remarkable.")
    _msg(ch_general, "Nicole Torres", PEOPLE["Nicole Torres"],
         "Well deserved. The engineering team has been shipping at an insane pace. Proud of this crew.")
    _msg(ch_general, "Alex Rivera", PEOPLE["Alex Rivera"],
         "Also a reminder: all-hands is tomorrow at 2pm. I'll be sharing Q1 OKRs and some exciting partnership news. Please block your calendars.")
    _msg(ch_general, "Elena Rodriguez", PEOPLE["Elena Rodriguez"],
         "Will there be a recording for folks who can't make it live?")
    _msg(ch_general, "Alex Rivera", PEOPLE["Alex Rivera"],
         "Yes, we'll record it and post in #general afterwards.")
    _msg(ch_general, "David Park", PEOPLE["David Park"],
         "Heads up: scheduled maintenance window tonight 11pm-1am EST for the database migration. Expect ~5 min of downtime.")
    _msg(ch_general, "Sarah Kim", PEOPLE["Sarah Kim"],
         "Thanks for the heads up David. I'll add it to the status page.")

    print("Seeding #engineering...")
    msg_counter[0] = 0
    _msg(ch_eng, "Nicole Torres", PEOPLE["Nicole Torres"],
         "Team standup notes: Document analysis pipeline is 80% done. @Marcus how's the PDF parser coming along?")
    _msg(ch_eng, "Marcus Chen", PEOPLE["Marcus Chen"],
         "PDF parser is working for text-based PDFs. Scanned PDFs with OCR are trickier. I'm evaluating Tesseract vs Google Vision API. Tesseract is free but accuracy is ~85%. Vision API is 95%+ but costs $1.50/1000 pages.")
    _msg(ch_eng, "Nicole Torres", PEOPLE["Nicole Torres"],
         "Let's go with Tesseract for v1 and add Vision API as a premium tier feature. Keep the cost structure simple for now.")
    _msg(ch_eng, "James Wilson", PEOPLE["James Wilson"],
         "SSO integration is coming along. Got SAML working with Okta in staging. Azure AD is next. One issue: the callback URL handling is brittle when behind our load balancer. Working on a fix.")
    _msg(ch_eng, "David Park", PEOPLE["David Park"],
         "James — I can help with the LB config. We need to set X-Forwarded-Proto headers properly. I'll push a fix to the nginx config today.")
    _msg(ch_eng, "James Wilson", PEOPLE["James Wilson"],
         "That would be great, thanks David!")
    _msg(ch_eng, "Marcus Chen", PEOPLE["Marcus Chen"],
         "PR is up for the context window optimization: #247. Reduced token usage by 35% on large documents using sliding window with overlap. Reviews welcome.")
    _msg(ch_eng, "Nicole Torres", PEOPLE["Nicole Torres"],
         "Nice work Marcus. I'll review this afternoon. 35% reduction is huge for our API costs.")
    _msg(ch_eng, "David Park", PEOPLE["David Park"],
         "Also: I've set up Grafana dashboards for the new multi-tenant staging env. 3 simulated tenants running. CPU and memory look good under load. Link in the wiki.")

    print("Seeding #product...")
    msg_counter[0] = 0
    _msg(ch_product, "Sarah Kim", PEOPLE["Sarah Kim"],
         "Sharing the updated roadmap for Q1. Key changes: moved Slack integration to Q2, added SOC2 compliance as a Q1 priority based on customer feedback.")
    _msg(ch_product, "Elena Rodriguez", PEOPLE["Elena Rodriguez"],
         "The document viewer mockups are ready for review. I went with a split-pane layout: document preview on the left, AI analysis on the right. Figma link: [mockups]")
    _msg(ch_product, "Sarah Kim", PEOPLE["Sarah Kim"],
         "Love the split-pane approach Elena. Can we add a collapsible panel for the entity list? Some docs have 20+ entities and it gets crowded.")
    _msg(ch_product, "Elena Rodriguez", PEOPLE["Elena Rodriguez"],
         "Good call. I'll add a collapsible sidebar with tags/chips for entities. Should also be filterable. Updated designs by tomorrow.")
    _msg(ch_product, "Alex Rivera", PEOPLE["Alex Rivera"],
         "Customer request from Acme Corp: they want custom branding (logo, colors) on their tenant. How much effort is that?")
    _msg(ch_product, "Sarah Kim", PEOPLE["Sarah Kim"],
         "Moderate effort. We'd need a tenant settings page + CSS variable overrides. Maybe 2 sprints. I'll spec it out and add to the backlog.")
    _msg(ch_product, "Maya Johnson", PEOPLE["Maya Johnson"],
         "FYI: 3 more enterprise prospects asked about white-labeling this week. It's becoming a pattern. Might be worth prioritizing.")

    print("Seeding #random...")
    msg_counter[0] = 0
    _msg(ch_random, "James Wilson", PEOPLE["James Wilson"],
         "Anyone else's coffee machine broken today or is it just me suffering?")
    _msg(ch_random, "Elena Rodriguez", PEOPLE["Elena Rodriguez"],
         "It's been broken since Monday. I've switched to tea. Life is pain.")
    _msg(ch_random, "David Park", PEOPLE["David Park"],
         "I filed a ticket with facilities. They said 'we're looking into it.' Which we all know means never.")
    _msg(ch_random, "Marcus Chen", PEOPLE["Marcus Chen"],
         "I just bring my own aeropress. Problem solved. Also tastes 10x better.")
    _msg(ch_random, "Maya Johnson", PEOPLE["Maya Johnson"],
         "Fun fact: I just learned that the team has collectively consumed 847 cups of coffee since we started tracking in the kitchen. We are a caffeine-powered startup.")
    _msg(ch_random, "Alex Rivera", PEOPLE["Alex Rivera"],
         "New coffee machine budget: approved. Consider it a Series A celebration gift.")
    _msg(ch_random, "James Wilson", PEOPLE["James Wilson"],
         "THE GOAT.")
    _msg(ch_random, "Elena Rodriguez", PEOPLE["Elena Rodriguez"],
         "Alex I take back everything I said in my last 1-on-1.")

    print("Seeding #sales...")
    msg_counter[0] = 0
    _msg(ch_sales, "Maya Johnson", PEOPLE["Maya Johnson"],
         "Pipeline update: 3 enterprise deals in final stages. Acme Corp ($18K/mo expansion), NexGen Analytics ($12K/mo new), TechFlow Inc ($8K/mo new). Total pipeline: $456K ARR.")
    _msg(ch_sales, "Alex Rivera", PEOPLE["Alex Rivera"],
         "Great pipeline Maya. What's the blocker on NexGen? They've been in final stage for 2 weeks.")
    _msg(ch_sales, "Maya Johnson", PEOPLE["Maya Johnson"],
         "Their security team wants SOC2. I told them it's on our Q1 roadmap. They're willing to wait if we can give a firm date.")
    _msg(ch_sales, "Sarah Kim", PEOPLE["Sarah Kim"],
         "We're targeting end of March for SOC2 Type I. I can put together a timeline doc for them if that helps close.")
    _msg(ch_sales, "Maya Johnson", PEOPLE["Maya Johnson"],
         "That would be perfect Sarah. A formal timeline doc would give their CISO the confidence to approve.")
    _msg(ch_sales, "Alex Rivera", PEOPLE["Alex Rivera"],
         "Let's also loop Nicole in on the SOC2 timeline. Some of the technical controls need engineering sign-off.")

    print("\nDone! Team chat seeded successfully.")
    channels = db.get_channels()
    for ch in channels:
        msgs = db.get_channel_messages(ch["id"])
        print(f"  #{ch['name']}: {len(msgs)} messages")


if __name__ == "__main__":
    main()
