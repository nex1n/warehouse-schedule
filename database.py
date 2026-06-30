import os
import datetime
from typing import Optional, List
from dotenv import load_dotenv
from sqlalchemy import create_engine, String, Boolean, Numeric, Date, ForeignKey, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# 1. Загрузка переменных окружения
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Если переменная окружения отсутствует, принудительно завершаем работу скрипта
if not DATABASE_URL:
    raise RuntimeError(
        "❌ CRITICAL ERROR: 'DATABASE_URL' environment variable is missing!\n"
        "Please configure the PostgreSQL database connection string."
    )

# Создаем движок только для целевой базы данных (PostgreSQL)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Автоматически проверяет живое ли соединение перед отправкой запросов
    pool_recycle=1800,   # Сбрасывает старые соединения каждые 30 минут, чтобы избежать таймаутов со стороны БД
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Базовый декларативный класс
class Base(DeclarativeBase):
    pass

# ==============================================================================
# МОДЕЛЬ: WORKER (Сотрудники)
# ==============================================================================
class Worker(Base):
    __tablename__ = "workers"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    preferred_object: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    projectcode: Mapped[str] = mapped_column(String(20), nullable=False)
    cc: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    fixed_course_days: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_fired: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    vacations: Mapped[List["Vacation"]] = relationship(
        "Vacation", back_populates="worker", cascade="all, delete-orphan", lazy="selectin"
    )
    shifts: Mapped[List["Schedule"]] = relationship(
        "Schedule", back_populates="worker", cascade="all, delete-orphan"
    )

# ==============================================================================
# МОДЕЛЬ: VACATION (Отпуска)
# ==============================================================================
class Vacation(Base):
    __tablename__ = "vacations"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    worker: Mapped["Worker"] = relationship("Worker", back_populates="vacations")

# ==============================================================================
# МОДЕЛЬ: SCHEDULE (Смены)
# ==============================================================================
class Schedule(Base):
    __tablename__ = "schedule"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    worker_id: Mapped[int] = mapped_column(ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    object: Mapped[str] = mapped_column(String(50), nullable=False)
    sub_object: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hours: Mapped[float] = mapped_column(Numeric(4, 2), default=8.00, nullable=False)

    worker: Mapped["Worker"] = relationship("Worker", back_populates="shifts", lazy="joined")

# ==============================================================================
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ==============================================================================
def check_db_connection() -> bool:
    """Проверяет реальную доступность базы данных, отправляя легкий пинг-запрос."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False

def init_db() -> None:
    """Создает все таблицы в PostgreSQL, если они еще не созданы."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Возвращает чистую сессию базы данных."""
    return SessionLocal()