import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

TOKEN = "9105045900:AAFTRIJXuXvRb5ktByT_mdamMtefBRkRxZw"
ADMIN_USER_ID = 8514764458

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()

class AdminManageState(StatesGroup):
    waiting_for_channel_to_add = State()
    waiting_for_confirmation_to_add = State()
    waiting_for_channel_to_remove = State()
    waiting_for_confirmation_to_remove = State()

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 অ্যাডমিন হন", callback_data="btn_add_admin")],
        [InlineKeyboardButton(text="❌ অ্যাডমিন কাটুন", callback_data="btn_remove_admin")]
    ])

def get_confirm_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ কনফার্ম করুন", callback_data="confirm_action")],
        [InlineKeyboardButton(text="❌ বাতিল করুন", callback_data="cancel_action")]
    ])

@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != ADMIN_USER_ID:
        await message.answer("⚠️ আপনার এই বট ব্যবহারের অনুমতি নেই।")
        return
    await message.answer("স্বাগতম! চ্যানেল ম্যানেজমেন্ট প্যানেলে আপনাকে স্বাগতম। নিচে থেকে আপনার অপশন বেছে নিন:", reply_markup=get_main_menu())

@router.callback_query(F.data == "btn_add_admin")
async def start_add_admin(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("অনুমতি নেই!", show_alert=True)
        return
    await callback.message.edit_text("📢 দয়া করে আপনার চ্যানেলটির পাবলিক লিংক (যেমন: `@mychannel`) অথবা চ্যাট আইডি দিন:")
    await state.set_state(AdminManageState.waiting_for_channel_to_add)
    await callback.answer()

@router.message(AdminManageState.waiting_for_channel_to_add)
async def process_channel_link_for_add(message: Message, state: FSMContext):
    channel_input = message.text.strip()
    try:
        chat_member = await bot.get_chat_member(chat_id=channel_input, user_id=bot.id)
        if chat_member.status not in ["administrator", "creator"]:
            await message.answer("❌ এখনো বটকে চ্যানেলে অ্যাডমিন দেওয়া হয়নি। আগে বটকে চ্যানেলের অ্যাডমিন করুন।", reply_markup=get_main_menu())
            await state.clear()
            return
        chat_info = await bot.get_chat(chat_id=channel_input)
        await state.update_data(channel_id=channel_input, channel_title=chat_info.title)
        await message.answer(f"📢 **চ্যানেল:** {chat_info.title}\n\nআপনি কি নিশ্চিতভাবে এই চ্যানেলের অ্যাডমিন হতে চান?", reply_markup=get_confirm_menu())
        await state.set_state(AdminManageState.waiting_for_confirmation_to_add)
    except Exception as e:
        await message.answer(f"❌ ভুল লিংক বা বট চ্যানেলটিতে যুক্ত নেই। ত্রুটি: {str(e)}", reply_markup=get_main_menu())
        await state.clear()

@router.callback_query(AdminManageState.waiting_for_confirmation_to_add, F.data.in_(["confirm_action", "cancel_action"]))
async def confirm_add_admin_action(callback: CallbackQuery, state: FSMContext):
    if callback.data == "cancel_action":
        await callback.message.edit_text("❌ প্রসেস বাতিল করা হয়েছে।", reply_markup=get_main_menu())
        await state.clear()
        return
    data = await state.get_data()
    channel_id = data.get("channel_id")
    try:
        await bot.promote_chat_member(
            chat_id=channel_id,
            user_id=ADMIN_USER_ID,
            is_anonymous=False,
            can_manage_chat=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_delete_messages=True,
            can_invite_users=True,
            can_manage_video_chats=True,
            can_promote_members=False,
            can_restrict_members=True
        )
        await callback.message.edit_text("🎉 সফল! আপনাকে এই চ্যানেলের অ্যাডমিন বানিয়ে দেওয়া হয়েছে।", reply_markup=get_main_menu())
    except Exception as e:
        await callback.message.edit_text(f"❌ সমস্যা হয়েছে। ত্রুটি: {str(e)}", reply_markup=get_main_menu())
    await state.clear()

@router.callback_query(F.data == "btn_remove_admin")
async def start_remove_admin(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_USER_ID:
        await callback.answer("অনুমতি নেই!", show_alert=True)
        return
    await callback.message.edit_text("📢 যে চ্যানেল থেকে আপনার অ্যাডমিন অধিকার সরাতে চান, সেটির লিংক দিন:")
    await state.set_state(AdminManageState.waiting_for_channel_to_remove)
    await callback.answer()

@router.message(AdminManageState.waiting_for_channel_to_remove)
async def process_channel_link_for_remove(message: Message, state: FSMContext):
    channel_input = message.text.strip()
    try:
        chat_info = await bot.get_chat(chat_id=channel_input)
        await state.update_data(channel_id=channel_input, channel_title=chat_info.title)
        await message.answer(f"📢 **চ্যানেল:** {chat_info.title}\n\nআপনি কি নিশ্চিতভাবে এই চ্যানেল থেকে অ্যাডমিন সরাতে চান?", reply_markup=get_confirm_menu())
        await state.set_state(AdminManageState.waiting_for_confirmation_to_remove)
    except Exception as e:
        await message.answer(f"❌ সঠিক লিংক দিন। ত্রুটি: {str(e)}", reply_markup=get_main_menu())
        await state.clear()

@router.callback_query(AdminManageState.waiting_for_confirmation_to_remove, F.data.in_(["confirm_action", "cancel_action"]))
async def confirm_remove_admin_action(callback: CallbackQuery, state: FSMContext):
    if callback.data == "cancel_action":
        await callback.message.edit_text("❌ বাতিল করা হয়েছে।", reply_markup=get_main_menu())
        await state.clear()
        return
    data = await state.get_data()
    channel_id = data.get("channel_id")
    try:
        await bot.promote_chat_member(
            chat_id=channel_id,
            user_id=ADMIN_USER_ID,
            is_anonymous=False,
            can_manage_chat=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_manage_video_chats=False,
            can_promote_members=False,
            can_restrict_members=False
        )
        await callback.message.edit_text("✅ সফল! আপনার অ্যাডমিন অধিকার সরিয়ে নেওয়া হয়েছে।", reply_markup=get_main_menu())
    except Exception as e:
        await callback.message.edit_text(f"❌ ত্রুটি: {str(e)}", reply_markup=get_main_menu())
    await state.clear()

async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
