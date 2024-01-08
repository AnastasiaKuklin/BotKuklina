from config_reader import config
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters.command import Command
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from states import File
import io
from aiogram.fsm.storage.memory import MemoryStorage
import pandas as pd

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher(storage=MemoryStorage())
router = Router()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Здравствуйте! \n"
                         "Моя работа анализировать ваш exel файл с отметками студентов. Чтобы начать работу, пожалуйста, пропишите команду /file.")

    
@router.message(StateFilter(None), Command("file"))
async def cmd_file(message: Message, state: FSMContext):
    await message.answer(
        text="Пожалуйста, отправьте мне тот самый exel файл с оценками студентов")
    await state.set_state(File.sending_file)
    
@router.message(File.sending_file)
async def save_doc(message: Message, state: FSMContext):
    try: 
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        my_object = io.BytesIO()
        MyBinaryIO = await bot.download_file(file_path, my_object)
        await state.update_data(file = MyBinaryIO)
        await message.answer("Файл успешно загружен. Пожалуйста, подожите чуть-чуть...")
        data = pd.read_excel(MyBinaryIO)
        try:
            grup = data['Группа'].unique()
            grup_str = ', '.join(grup)
            await state.set_state(File.groupName)
            await message.answer(f'В моей базе данных храниться информации таких групп как: {grup_str}')
            await message.answer(
            "Введите номер группы: ")
        except:
            await message.answer(f"Загрузите другой файл, данный файл не подлежит обрабоке.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при загрузке файла. {e}")
    
@router.message(File.groupName)
async def search_group(message: Message, state: FSMContext):
    await message.answer("Файл обрабатывается. Это может занять несколько секунд или минут.")
    await state.update_data(groupName = message.text)
    group = await state.get_data()
    data = pd.read_excel(group['file'])
    try:
        await message.answer(f"Номер вашей группы:  {group['groupName']}")
        kol = data['Группа'].str.contains(group['groupName']).sum()
        if kol == 0:
            await message.answer('К сожалению группы с таким номером не существует.')
        else:
            try:
                kol_grades = data['Оценка'].notna().sum()
                kol_grades_group = ((data['Группа']== group['groupName']) & (data['Оценка'].notna())).sum()
                kol_stud = len(data[(data['Группа']== group['groupName']) & (data['Оценка'].notna())].drop_duplicates(subset=['Личный номер студента']))
                id_stud = ((data[(data['Группа']== group['groupName']) & (data['Оценка'].notna())].drop_duplicates(subset=['Личный номер студента']))['Личный номер студента']).tolist()
                form_contr = ((data[(data['Группа']==group['groupName']) & (data['Оценка'].notna())].drop_duplicates(subset=['Уровень контроля']))['Уровень контроля']).tolist()
                years = ((data[(data['Группа']== group['groupName']) & (data['Оценка'].notna())].drop_duplicates(subset=['Год']))['Год']).tolist()
                await message.answer(f'В исходном датасете содержалось {kol_grades} оценок, из них {kol_grades_group} оценок относятся к группе ПИ101. В датасете находятся оценки {kol_stud} студентов со следующими личными номерами по ПИ101: {id_stud}. Используемые формы контроля: {form_contr}. Данные представлены по следующим учебным годам: {years}')
            except:
                await message.answer(f"Загрузите другой файл, данный файл не подлежит обрабоке.")             
    except:
        await message.answer(f"Загрузите другой файл, данный файл не подлежит обрабоке.")                                

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())