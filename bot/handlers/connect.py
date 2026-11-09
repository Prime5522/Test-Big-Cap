from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message
from bot.database import db

async def verify_and_add(c: Client, m: Message, chat_target):
    user_id = m.from_user.id
    try:
        chat = await c.get_chat(chat_target)
    except Exception:
        return await m.reply_text("❌ <b>চ্যানেলটি খুঁজে পাওয়া যায়নি!</b>\nবটটিকে চ্যানেলে অ্যাডমিন করেছেন কি না নিশ্চিত করুন।")

    if chat.type.name != "CHANNEL":
        return await m.reply_text("⚠️ এটি কোনো চ্যানেল নয়! শুধুমাত্র চ্যানেলে বট কানেক্ট করা যাবে।")

    # ১. চেক করুন বট চ্যানেলে অ্যাডমিন কি না
    try:
        bot_member = await c.get_chat_member(chat.id, "me")
        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            return await m.reply_text("⚠️ <b>বটটি এই চ্যানেলে অ্যাডমিন নয়!</b>\nদয়া করে মেসেজ পোস্ট ও এডিট পারমিশন দিয়ে বটকে অ্যাডমিন করুন।")
    except Exception:
        return await m.reply_text("⚠️ বটটি আপনার চ্যানেলে নেই বা প্রয়োজনীয় পারমিশন নেই।")

    # ২. চেক করুন যে ইউজার কানেক্ট করতে চাচ্ছে সে চ্যানেলের অ্যাডমিন/মালিক কি না
    try:
        user_member = await c.get_chat_member(chat.id, user_id)
        if user_member.status not in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR):
            return await m.reply_text("❌ <b>অ্যাক্সেস ডিনাইড!</b> আপনি এই চ্যানেলের অ্যাডমিন বা ওনার নন।")
    except Exception:
        return await m.reply_text("❌ আপনি এই চ্যানেলে অ্যাডমিন নন।")

    # ৩. ডেটাবেজে অ্যাডমিন হিসেবে ইউজারকে যুক্ত করা
    await db.add_channel(chat.id, chat.title or str(chat.id), owner_id=user_id)
    await db.channels.update_one({"_id": chat.id}, {"$addToSet": {"admins": user_id}})

    await m.reply_text(
        f"✅ <b>চ্যানেল সফলভাবে কানেক্ট হয়েছে!</b>\n\n"
        f"📢 <b>নাম:</b> {chat.title}\n"
        f"🆔 <b>আইডি:</b> <code>{chat.id}</code>\n\n"
        f"🌐 এখন আপনি <b>Web Panel</b> রিফ্রেশ করলেই এই চ্যানেলটি দেখতে পাবেন।"
    )

# ১. /connect কমান্ড দিয়ে কানেক্ট করা
@Client.on_message(filters.private & filters.command("connect"))
async def connect_cmd(c: Client, m: Message):
    parts = m.text.split(None, 1)
    if len(parts) < 2:
        return await m.reply_text(
            "📌 <b>চ্যানেল কানেক্ট করার নিয়ম:</b>\n\n"
            "১. বটকে আপনার চ্যানেলে অ্যাডমিন বানান।\n"
            "২. এখানে কমান্ড দিন: <code>/connect @your_channel</code> অথবা ID: <code>/connect -100xxxxxxxxx</code>\n\n"
            "💡 <i>অথবা আপনার চ্যানেল থেকে যেকোনো একটি পোস্ট এই বটে <b>Forward</b> করুন!</i>"
        )
    target = parts[1].strip()
    if target.lstrip("-").isdigit():
        target = int(target)
    await verify_and_add(c, m, target)

# ২. চ্যানেল থেকে মেসেজ Forward করলে অটো-কানেক্ট
@Client.on_message(filters.private & filters.forwarded)
async def forward_connect(c: Client, m: Message):
    if m.forward_from_chat and m.forward_from_chat.type.name == "CHANNEL":
        await verify_and_add(c, m, m.forward_from_chat.id)
