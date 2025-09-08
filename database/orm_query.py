import uuid
import json

from sqlalchemy import update, delete, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.future import select
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from typing import Optional, Tuple
from typing import List


from database.models import Company, Branch, User, CardTransaction, Channel, UserType, StatusType


async def generate_unique_number():
    unique_id = str(uuid.uuid4().int)[:6]
    return int(unique_id)


################################ User #####################################


async def orm_add_user(
    session: AsyncSession,
    telegram_id: int,
    full_name: str | None = None,
    user_type: str | None = None,
    login: str | None = None,
    password: str | None = None,
    user_1c_id: int | None = None,
    company_id: int | None = None,
    branch_id: int | None = None,
) -> tuple[User, bool]:

    query = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(query)
    existing_user = result.scalar_one_or_none()

    if existing_user is None:
        user_type_enum = UserType(user_type) if user_type else UserType.CASHIER

        new_user = User(
            telegram_id=telegram_id,
            full_name=full_name or "No name",
            user_type=user_type_enum,
            login=login,
            password=password,
            user_1c_id=user_1c_id,
            company_id=company_id,
            branch_id=branch_id,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user, True
    else:
        return existing_user, False


async def get_admin_users(session: AsyncSession):
    stmt = select(User.telegram_id).where(User.user_type == UserType.ADMIN)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_chief_cashier_users(session: AsyncSession, company_id: int):
    stmt = select(User.telegram_id).where(
        (User.user_type == UserType.CHIEF_CASHIER) & (User.company_id == company_id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_admin_users_by_company(session: AsyncSession, company_id: int):
    stmt = (
        select(User.telegram_id)
        .where(User.user_type == UserType.ADMIN, User.company_id == company_id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def select_user(telegram_id: int, session: AsyncSession):
    query = select(User).filter(User.telegram_id == telegram_id)
    result = await session.execute(query)
    user = result.scalars().first()
    print(f"Selected User: {user}")
    return user


async def update_user_activity(session: AsyncSession, telegram_id: int) -> bool:
    stmt = (
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(
            is_active=True,
            status_type=StatusType.COMPLETED
        )
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def is_user_active(telegram_id: int, session: AsyncSession) -> bool | None:
    try:
        query = select(User.is_active).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    except Exception as e:
        print(f"Xatolik: {e}")
        return None


async def select_user_by_phone_number(session: AsyncSession, phone_number: str):
    query = select(User).filter(User.phone == phone_number)
    result = await session.execute(query)
    return result.scalars().first()


async def get_user_full_name_by_id(session: AsyncSession, user_id: int):
    query = select(User.full_name).filter(User.id == user_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def orm_clear_user_branch(session: AsyncSession, telegram_id: int):
    query = (
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(branch_id=None)
    )
    await session.execute(query)
    await session.commit()


async def update_user_phone_number(session: AsyncSession, phone_number: str, telegram_id: int):
    query = (
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(phone=phone_number)
    )
    await session.execute(query)
    await session.commit()


async def update_user_branch_id(session: AsyncSession, branch_id: int, telegram_id: int):
    query = (
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(branch_id=branch_id)
    )
    await session.execute(query)
    await session.commit()


async def select_all_users(session: AsyncSession):
    query = select(User)
    result = await session.execute(query)
    return result.scalars().all()


async def select_all_order_users(session: AsyncSession):
    query = select(User).where(User.is_active==True)
    result = await session.execute(query)
    return result.scalars().all()


async def delete_all_users(session: AsyncSession):
    try:
        query = delete(User)
        await session.execute(query)
        await session.commit()

    except Exception as e:
        await session.rollback()
        print(f"Error deleting users: {e}")


async def count_daily_users(session: AsyncSession):
    today = datetime.now().date()
    query = select(func.count()).where(User.joined_at >= today)
    result = await session.execute(query)
    return result.scalar()


async def count_weekly_users(session: AsyncSession):
    last_week = datetime.now().date() - timedelta(days=7)
    query = select(func.count()).where(User.joined_at >= last_week)
    result = await session.execute(query)
    return result.scalar()


async def count_monthly_users(session: AsyncSession):
    last_month = datetime.now().date() - timedelta(days=30)
    query = select(func.count()).where(User.joined_at >= last_month)
    result = await session.execute(query)
    return result.scalar()


async def count_users(session: AsyncSession):
    query = select(func.count()).select_from(User)
    result = await session.execute(query)
    return result.scalar()


async def orm_admin_exist(session: AsyncSession, admin_id: int) -> bool:
    stmt = select(exists().where(User.telegram_id == admin_id))
    result = await session.execute(stmt)
    return result.scalar()


async def orm_add_admin(
    session: AsyncSession,
    telegram_id: int,
    full_name: str,
    company_id: int,
    branch_id: int,
    user_type: UserType = UserType.ADMIN,   # default ADMIN
):
    new_admin = User(
        telegram_id=telegram_id,
        full_name=full_name,
        company_id=company_id,
        branch_id=branch_id,
        user_type=user_type,
        is_active=True
    )
    session.add(new_admin)

    try:
        await session.commit()
        await session.refresh(new_admin)
        return new_admin
    except IntegrityError:
        await session.rollback()
        return None


async def orm_delete_admin_by_id(session: AsyncSession, admin_id: int):
    query = delete(User).where(User.telegram_id == admin_id)
    await session.execute(query)
    await session.commit()


async def orm_delete_by_id(session: AsyncSession, telegram_id: int):
    query = delete(User).where(User.telegram_id == telegram_id)
    await session.execute(query)
    await session.commit()


######################## Channel #######################################


async def create_or_update_channel(session: AsyncSession, data: dict):
    result = await session.execute(
        select(Channel).where(Channel.category_id == int(data["category_id"]))
    )
    channel = result.scalars().first()
    if channel:
        channel.channel_id = data["channel_id"]
    else:
        channel = Channel(
            category_id=int(data["category_id"]),
            channel_id=int(data["channel_id"])
        )
        session.add(channel)

    await session.commit()
    return channel


async def select_all_channels(session: AsyncSession):
    query = select(Channel.channel_id, Channel.category_id)
    result = await session.execute(query)
    return result.fetchall()


async def select_channel(session: AsyncSession, channel_id: int):
    query = select(Channel).where(Channel.channel_id == channel_id)
    result = await session.execute(query)
    return result.scalars().first()


async def orm_channel_id(session: AsyncSession, category_id: int):
    query = select(Channel.channel_id).where(Channel.category_id == category_id)
    result = await session.execute(query)
    return result.scalars().first()


async def delete_channels(session: AsyncSession):
    query = delete(Channel)
    await session.execute(query)
    await session.commit()


async def delete_channel_by_id(session: AsyncSession, category_id: int):
    query = delete(Channel).where(Channel.category_id == category_id)
    await session.execute(query)
    await session.commit()


###################### Branch #######################


async def orm_update_branch(session: AsyncSession, branch_id: int, data):
    query = (
        update(Branch)
        .where(Branch.id == branch_id)
        .values(
            name_uz=data["name_uz"],
            name_ru=data["name_ru"],
            location_uz=data["location_uz"],
            location_ru=data["location_ru"],
        )
    )
    await session.execute(query)
    await session.commit()


async def orm_select_all_branch(session: AsyncSession):
    query = select(Branch.id, Branch.name)
    result = await session.execute(query)
    return result.all()


async def orm_select_branch_by_id(branch_id: int, session: AsyncSession):
    query = select(Branch.id, Branch.name).where(Branch.id == branch_id)
    result = await session.execute(query)
    return result.fetchone()


async def orm_select_one_branch_id_by_company_id(company_id: int, session: AsyncSession):
    query = select(Branch.id).where(Branch.company_id == company_id)
    result = await session.execute(query)
    row = result.fetchone()
    return row[0] if row else None


async def orm_delete_branch_by_id(session: AsyncSession, branch_id: int):
    query = delete(Branch).where(Branch.id == branch_id)
    await session.execute(query)
    await session.commit()


##################### Company #####################


async def orm_add_company(session: AsyncSession, data: dict):
    obj = Company(
        name=data["name"],
        branch_url=data["branch_url"],
        terminals_url=data["terminals_url"],
        login=data["login"],
        password=data["password"]
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def select_all_companies(session: AsyncSession):
    query = select(Company)
    result = await session.execute(query)
    return result.scalars().all()


async def company_name_exist(session: AsyncSession, name: str) -> bool:
    stmt = select(Company).where(Company.name == name)
    result = await session.execute(stmt)
    return result.scalars().first() is not None


async def company_branches_link_exist(session: AsyncSession, branch_url: str) -> bool:
    stmt = select(Company).where(Company.branch_url == branch_url)
    result = await session.execute(stmt)
    return result.scalars().first() is not None


async def company_confirm_terminal_link_exist(session: AsyncSession, terminals_url: str) -> bool:
    stmt = select(Company).where(Company.terminals_url == terminals_url)
    result = await session.execute(stmt)
    return result.scalars().first() is not None


async def get_company_id_by_name(session: AsyncSession, name: str) -> int | None:
    stmt = select(Company.id).where(Company.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_company_url_by_id(session: AsyncSession, company_id: int) -> Optional[Tuple[str, str, str]]:
    stmt = select(Company.branch_url, Company.login, Company.password).where(Company.id == company_id)
    result = await session.execute(stmt)
    return result.one_or_none()


async def get_company_name_by_id(session: AsyncSession, company_id: int) -> str | None:
    stmt = select(Company.name).where(Company.id == company_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_company_name(session: AsyncSession, company_id: int, new_name: str) -> bool:
    stmt = (
        update(Company)
        .where(Company.id == company_id)
        .values(name=new_name)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_company_branch_link(session: AsyncSession, company_id: int, new_link: str) -> bool:
    stmt = (
        update(Company)
        .where(Company.id == company_id)
        .values(branch_url=new_link)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_company_terminal_link(session: AsyncSession, company_id: int, new_link: str) -> bool:
    stmt = (
        update(Company)
        .where(Company.id == company_id)
        .values(terminals_url=new_link)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_company_login(session: AsyncSession, company_id: int, new_login: str) -> bool:
    stmt = (
        update(Company)
        .where(Company.id == company_id)
        .values(login=new_login)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_company_password(session: AsyncSession, company_id: int, new_password: str) -> bool:
    stmt = (
        update(Company)
        .where(Company.id == company_id)
        .values(password=new_password)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def get_terminals_url_by_id(session: AsyncSession, company_id: int) -> Optional[Tuple[str, str, str]]:
    stmt = select(Company.terminals_url, Company.login, Company.password).where(Company.id == company_id)
    result = await session.execute(stmt)
    return result.one_or_none()


async def delete_company_by_name(session: AsyncSession, name: str) -> bool:
    stmt = select(Company).where(Company.name == name)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        return False

    await session.delete(company)
    await session.commit()
    return True


##################### Branch #####################


async def orm_add_branch(session: AsyncSession, data: dict):
    obj = Branch(
        company_id=data["company_id"],
        name=data["name"],
        cashiers_url=data["cashiers_url"],
        chief_cashiers_url=data["chief_cashiers_url"],
        check_pass_url=data["check_pass_url"],
        transaction_url=data["transaction_url"],
        list_transaction_url=data["get_transaction_url"],
        check_transaction_url=data["check_transaction_url"],
        login=data["login"],
        password=data["password"]
    )
    session.add(obj)
    await session.commit()
    await session.refresh(obj)
    return obj


async def cashier_link_exist(session: AsyncSession, cashiers_url: str) -> Branch | None:
    stmt = select(Branch).where(Branch.cashiers_url == cashiers_url)
    result = await session.execute(stmt)
    return result.scalars().first()


async def chief_cashier_link_exist(session: AsyncSession, chief_cashiers_url: str) -> Branch | None:
    stmt = select(Branch).where(Branch.chief_cashiers_url == chief_cashiers_url)
    result = await session.execute(stmt)
    return result.scalars().first()


async def pass_check_link_exist(session: AsyncSession, check_pass_url: str) -> Branch | None:
    stmt = select(Branch).where(Branch.check_pass_url == check_pass_url)
    result = await session.execute(stmt)
    return result.scalars().first()


async def transaction_link_exist(session: AsyncSession, transaction_url: str) -> Branch | None:
    stmt = select(Branch).where(Branch.transaction_url == transaction_url)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_transaction_link_exist(session: AsyncSession, get_transaction_url: str) -> Branch | None:
    stmt = select(Branch).where(Branch.list_transaction_url == get_transaction_url)
    result = await session.execute(stmt)
    return result.scalars().first()


async def check_transaction_link_exist(session: AsyncSession, check_transaction_url: str) -> Branch | None:
    stmt = select(Branch).where(Branch.check_transaction_url == check_transaction_url)
    result = await session.execute(stmt)
    return result.scalars().first()


async def get_branch_by_company_id(session: AsyncSession, company_id: int):
    stmt = select(Branch).where(Branch.company_id == company_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_branch_id_by_company_id(session: AsyncSession, company_id: int) -> int | None:
    stmt = select(Branch.id).where(Branch.company_id == company_id)
    result = await session.execute(stmt)
    branch_id = result.scalar_one_or_none()
    return branch_id



async def get_branch_id_by_name(session: AsyncSession, name: str) -> int | None:
    stmt = select(Branch.id).where(Branch.name == name)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_branch_transaction_url_by_id(session: AsyncSession, branch_id: int) -> Optional[str]:
    stmt = select(Branch.transaction_url).where(Branch.id == branch_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_branch_get_transaction_url_by_id(session: AsyncSession, branch_id: int) -> Optional[str]:
    stmt = select(Branch.list_transaction_url).where(Branch.id == branch_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_branch_confirm_transaction_url_by_id(session: AsyncSession, branch_id: int) -> Optional[str]:
    stmt = select(Branch.check_transaction_url).where(Branch.id == branch_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_branch_name(session: AsyncSession, branch_id: int, new_name: str) -> bool:
    stmt = (
        update(Branch)
        .where(Branch.id == branch_id)
        .values(name=new_name)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_branch_cashiers_url(session: AsyncSession, branch_id: int, new_link: str) -> bool:
    stmt = (
        update(Branch)
        .where(Branch.id == branch_id)
        .values(cashiers_url=new_link)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_branch_chief_cashiers_url(session: AsyncSession, branch_id: int, new_link: str) -> bool:
    stmt = (
        update(Branch)
        .where(Branch.id == branch_id)
        .values(chief_cashiers_url=new_link)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_branch_pass_url(session: AsyncSession, branch_id: int, new_link: str) -> bool:
    stmt = (
        update(Branch)
        .where(Branch.id == branch_id)
        .values(check_pass_url=new_link)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_branch_transaction_url(session: AsyncSession, branch_id: int, new_link: str) -> bool:
    stmt = (
        update(Branch)
        .where(Branch.id == branch_id)
        .values(transaction_url=new_link)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_branch_transactions_list_url(session: AsyncSession, branch_id: int, new_link: str) -> bool:
    stmt = (
        update(Branch)
        .where(Branch.id == branch_id)
        .values(list_transaction_url=new_link)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_branch_check_transaction_url(session: AsyncSession, branch_id: int, new_link: str) -> bool:
    stmt = (
        update(Branch)
        .where(Branch.id == branch_id)
        .values(check_transaction_url=new_link)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_branch_login(session: AsyncSession, branch_id: int, new_login: str) -> bool:
    stmt = (
        update(Branch)
        .where(Branch.id == branch_id)
        .values(login=new_login)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def update_branch_password(session: AsyncSession, branch_id: int, new_password: str) -> bool:
    stmt = (
        update(Branch)
        .where(Branch.id == branch_id)
        .values(password=new_password)
        .execution_options(synchronize_session="fetch")
    )
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0


async def delete_branch_by_name(session: AsyncSession, name: str) -> bool:
    stmt = select(Branch).where(Branch.name == name)
    result = await session.execute(stmt)
    branch = result.scalar_one_or_none()

    if not branch:
        return False

    await session.delete(branch)
    await session.commit()
    return True


async def get_cashier_by_id(session: AsyncSession, company_id: int) -> Optional[Tuple[str, str, str]]:
    stmt = select(Branch.cashiers_url, Branch.login, Branch.password).where(Branch.company_id == company_id)
    result = await session.execute(stmt)
    return result.first()


async def get_chief_cashier_by_id(session: AsyncSession, company_id: int) -> Optional[Tuple[str, str, str]]:
    stmt = select(Branch.chief_cashiers_url, Branch.login, Branch.password).where(Branch.company_id == company_id)
    result = await session.execute(stmt)
    return result.one_or_none()


async def get_pass_url_by_id(session: AsyncSession, company_id: int) -> Optional[Tuple[str, str, str]]:
    stmt = select(Branch.check_pass_url, Branch.login, Branch.password).where(Branch.company_id == company_id)
    result = await session.execute(stmt)
    return result.one_or_none()


######################## Transaction ########################


async def orm_add_transaction(
        session: AsyncSession,
        transaction_id: str,
        amount: int,
        card_type: str,
        cash_id: int | None = None,
        sender_terminal_id: int | None = None,
        receiver_terminal_id: int | None = None,
        sender_terminal_name: str | None = None,
        receiver_terminal_name: str | None = None,
        user_id: int | None = None,
        branch_id: int | None = None,
        company_id: int | None = None,
        comment: str | None = None,
        image: str | None = None,
        is_successful: bool = False,
        status_type: StatusType = StatusType.PENDING
):
    try:
        new_transaction = CardTransaction(
            transaction_id=transaction_id,
            amount=amount,
            card_type=card_type,
            cash_id=cash_id,
            sender_terminal_id=sender_terminal_id,
            receiver_terminal_id=receiver_terminal_id,
            sender_terminal_name=sender_terminal_name,
            receiver_terminal_name=receiver_terminal_name,
            user_id=user_id,
            branch_id=branch_id,
            company_id=company_id,
            comment=comment,
            image=image,
            is_successful=is_successful,
            status_type=status_type
        )

        session.add(new_transaction)
        await session.commit()
        await session.refresh(new_transaction)

        return new_transaction

    except Exception as e:
        await session.rollback()
        raise e


async def orm_complete_transaction(session: AsyncSession, transaction_id: str):
    stmt = select(CardTransaction).where(CardTransaction.transaction_id == transaction_id)
    result = await session.execute(stmt)
    transaction = result.scalar_one_or_none()
    if transaction:
        transaction.status_type = StatusType.COMPLETED
        transaction.is_successful = True

        await session.commit()
        await session.refresh(transaction)

        return transaction

    return None


async def get_transaction_by_id(
    session: AsyncSession,
    transaction_id: str
) -> Optional[CardTransaction]:
    stmt = select(CardTransaction).where(CardTransaction.transaction_id == transaction_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_transactions_by_company_id(
    session: AsyncSession,
    company_id: int
) -> List[CardTransaction]:
    stmt = select(CardTransaction).where(CardTransaction.company_id == company_id)
    result = await session.execute(stmt)
    return result.scalars().all()



async def get_transaction_by_chash_id(
    session: AsyncSession,
    transaction_id: str
) -> Optional[CardTransaction]:
    stmt = select(CardTransaction).where(CardTransaction.chash_id == chash_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def has_pending_transaction(
    session: AsyncSession,
    user_id: int,
    cash_id: int
) -> bool:
    stmt = (
        select(CardTransaction)
        .where(
            CardTransaction.user_id == user_id,
            CardTransaction.cash_id == cash_id,
            CardTransaction.status_type == StatusType.PENDING
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


async def delete_all_transactions(session: AsyncSession) -> None:
    stmt = delete(CardTransaction)
    await session.execute(stmt)
    await session.commit()


async def delete_transaction_by_id(session: AsyncSession, transaction_id: str) -> None:
    stmt = delete(CardTransaction).where(CardTransaction.transaction_id == transaction_id)
    result = await session.execute(stmt)
    if result.rowcount > 0:
        print(f"Tranzaksiya ID {transaction_id} muvaffaqiyatli o'chirildi.")
    else:
        print(f"Tranzaksiya ID {transaction_id} topilmadi.")

    await session.commit()


async def get_pending_transactions_by_company_id(
    session: AsyncSession,
    company_id: int
) -> List[CardTransaction]:
    stmt = (
        select(CardTransaction)
        .where(
            CardTransaction.company_id == company_id,
            CardTransaction.status_type == StatusType.PENDING
        )
    )
    result = await session.execute(stmt)
    return result.scalars().all()