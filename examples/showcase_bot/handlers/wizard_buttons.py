from vk_teams_async_bot import (
    Bot,
    CallbackDataFilter,
    CallbackDataRegexpFilter,
    CallbackQueryEvent,
    Dispatcher,
    FSMContext,
)

from ..keyboards import (
    main_menu_kb,
    wzb_confirm_kb,
    wzb_crust_kb,
    wzb_sauce_kb,
    wzb_size_kb,
)
from ..states import WizardButtonStates
from .utils import progress_bar, safe_edit


def register_wizard_buttons_handlers(dp: Dispatcher) -> None:
    @dp.callback_query(CallbackDataFilter("menu:wzb"))
    async def start_wizard(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(WizardButtonStates.choosing_size)
        await fsm_context.set_data({})
        await safe_edit(
            event,
            bot,
            f"Заказ пиццы {progress_bar(1, 4)}\n\nВыберите размер:",
            wzb_size_kb(),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^wzb:size:"))
    async def choose_size(event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext):
        size = event.callback_data.split(":")[2]
        await fsm_context.update_data(size=size)
        await fsm_context.set_state(WizardButtonStates.choosing_crust)
        await safe_edit(
            event,
            bot,
            f"Заказ пиццы {progress_bar(2, 4)}\n\nРазмер: {size}\nВыберите тесто:",
            wzb_crust_kb(),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^wzb:crust:"))
    async def choose_crust(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        crust = event.callback_data.split(":")[2]
        await fsm_context.update_data(crust=crust)
        await fsm_context.set_state(WizardButtonStates.choosing_sauce)
        data = await fsm_context.get_data()
        await safe_edit(
            event,
            bot,
            f"Заказ пиццы {progress_bar(3, 4)}\n\nРазмер: {data['size']}\nТесто: {crust}\nВыберите соус:",
            wzb_sauce_kb(),
        )

    @dp.callback_query(CallbackDataRegexpFilter(r"^wzb:sauce:"))
    async def choose_sauce(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        sauce = event.callback_data.split(":")[2]
        await fsm_context.update_data(sauce=sauce)
        await fsm_context.set_state(WizardButtonStates.confirm)
        data = await fsm_context.get_data()
        summary = (
            f"Заказ пиццы {progress_bar(4, 4)}\n\n"
            f"Размер: {data['size']}\n"
            f"Тесто: {data['crust']}\n"
            f"Соус: {sauce}\n\n"
            f"Подтвердить заказ?"
        )
        await safe_edit(event, bot, summary, wzb_confirm_kb())

    @dp.callback_query(CallbackDataFilter("wzb:confirm"))
    async def confirm_order(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        data = await fsm_context.get_data()
        await fsm_context.clear()
        summary = (
            f"Заказ подтвержден!\n\n"
            f"Размер: {data.get('size', '?')}\n"
            f"Тесто: {data.get('crust', '?')}\n"
            f"Соус: {data.get('sauce', '?')}\n\n"
            f"Ваша пицца уже в пути!"
        )
        await safe_edit(event, bot, summary, main_menu_kb())

    @dp.callback_query(CallbackDataFilter("wzb:cancel"))
    async def cancel_wizard(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.clear()
        await safe_edit(event, bot, "Заказ отменен. Главное меню.", main_menu_kb())

    @dp.callback_query(CallbackDataFilter("wzb:back:size"))
    async def back_to_size(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(WizardButtonStates.choosing_size)
        await safe_edit(
            event,
            bot,
            f"Заказ пиццы {progress_bar(1, 4)}\n\nВыберите размер:",
            wzb_size_kb(),
        )

    @dp.callback_query(CallbackDataFilter("wzb:back:crust"))
    async def back_to_crust(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(WizardButtonStates.choosing_crust)
        data = await fsm_context.get_data()
        await safe_edit(
            event,
            bot,
            f"Заказ пиццы {progress_bar(2, 4)}\n\nРазмер: {data.get('size', '?')}\nВыберите тесто:",
            wzb_crust_kb(),
        )

    @dp.callback_query(CallbackDataFilter("wzb:back:sauce"))
    async def back_to_sauce(
        event: CallbackQueryEvent, bot: Bot, fsm_context: FSMContext
    ):
        await fsm_context.set_state(WizardButtonStates.choosing_sauce)
        data = await fsm_context.get_data()
        await safe_edit(
            event,
            bot,
            f"Заказ пиццы {progress_bar(3, 4)}\n\nРазмер: {data.get('size', '?')}\nТесто: {data.get('crust', '?')}\nВыберите соус:",
            wzb_sauce_kb(),
        )
