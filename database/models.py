from sqlalchemy import DateTime, ForeignKey, Numeric, Integer, String, Text, BigInteger, Boolean, JSON, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates
from sqlalchemy_utils import URLType
from datetime import datetime
from sqlalchemy.sql import func
import re
import enum


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Company(Base):
    __tablename__ = 'company'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=True, unique=True)
    amount: Mapped[int] = mapped_column(BigInteger, default=0)
    branch_url: Mapped[str] = mapped_column(URLType, nullable=True) # barcha filiallar ro'yxati url
    terminals_url: Mapped[str] = mapped_column(URLType, nullable=True) # barcha kassalar ro'yxati url
    login: Mapped[str] = mapped_column(String(150), nullable=True)
    password: Mapped[str] = mapped_column(String(150), nullable=True)
    branches: Mapped[list["Branch"]] = relationship("Branch", back_populates="company", cascade="all, delete-orphan")


class Branch(Base):
    __tablename__ = 'branch'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)  # filial nomi
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    cashiers_url: Mapped[str] = mapped_column(URLType, nullable=True) # faqat kassirlar ro'yxati url
    chief_cashiers_url: Mapped[str] = mapped_column(URLType, nullable=True) # faqat bosh kassirlar ro'yxati url
    check_pass_url: Mapped[str] = mapped_column(URLType, nullable=True) # ro'yxatdan o'tishni tekshirish url
    transaction_url: Mapped[str] = mapped_column(URLType, nullable=True) # sverka create qilish uchun url
    list_transaction_url: Mapped[str] = mapped_column(URLType, nullable=True) # sverka list olish uchun url
    check_transaction_url: Mapped[str] = mapped_column(URLType, nullable=True)  # sverkani tekshirish uchun url
    login: Mapped[str] = mapped_column(String(150), nullable=True)
    password: Mapped[str] = mapped_column(String(150), nullable=True)
    company: Mapped["Company"] = relationship("Company", back_populates="branches")


class UserType(enum.Enum):
    ADMIN = "Admin"
    CASHIER = "Cashier"
    CHIEF_CASHIER = "ChiefCashier"


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=True)
    phone: Mapped[str] = mapped_column(String(13), nullable=True, unique=True)
    login: Mapped[str] = mapped_column(String(150), nullable=True)
    password: Mapped[str] = mapped_column(String(150), nullable=True)
    user_1c_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType), nullable=False, default=UserType.CASHIER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    branch_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    company: Mapped["Company"] = relationship("Company", backref="users")
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CardType(enum.Enum):
    TERMINAL = "Terminal"
    CASH = "Cash"


class StatusType(enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    CANCELED = "Canceled"


class CardTransaction(Base):
    __tablename__ = "card_transaction"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)  # external id
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    comment: Mapped[str] = mapped_column(String(355), nullable=True)
    card_type: Mapped[CardType] = mapped_column(Enum(CardType), nullable=False)
    status_type: Mapped[StatusType] = mapped_column(Enum(StatusType), default=StatusType.PENDING)
    sender_terminal_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    receiver_terminal_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    sender_terminal_name: Mapped[str] = mapped_column(String(150), nullable=True)
    receiver_terminal_name: Mapped[str] = mapped_column(String(150), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    user: Mapped["User"] = relationship("User", backref="transactions")
    branch_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    cash_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    is_successful: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Channel(Base):
    __tablename__ = 'channel'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)


