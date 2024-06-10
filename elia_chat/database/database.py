from contextlib import asynccontextmanager
from typing import AsyncGenerator, Union
from elia_chat.utils.locations import elia_chat_root
from elia_chat.utils.jsonu import json_stringify, json_parsef

# from sqlmodel import SQLModel
# from sqlmodel.ext.asyncio.session import AsyncSession
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

db_file_name = elia_chat_root() / ".db" / "elia.json"
"""File path of the database."""
# sqlite_url = f"sqlite+aiosqlite:///{sqlite_file_name}"
# engine = create_async_engine(sqlite_url)

DB_Creation_Error = Union[FileNotFoundError | PermissionError | OSError | Exception | None]

async def create_database() -> DB_Creation_Error:
    """Create a database and return any possible error that occurred during its creation."""
    db_initialization: dict = {

    }
    err: DB_Creation_Error = None

    try:
        # print(f"Creating database file at: {db_file_name}")

        # Create the file at the specified path
        db_file_name.parent.mkdir(parents=True, exist_ok=True)
        db_file_name.touch(exist_ok=True)
        
        # Write empty content to the file for initialization
        with db_file_name.open("w") as file:
            file.write(json_stringify(db_initialization))
        
    except FileNotFoundError as e:
        err = e
        print(f"Error creating database: path does not exist - {err}")

    except PermissionError as e:
        err = e
        print(f"Error creating database: Permission denied - {err}")

    except OSError as e:
        err = e
        print(f"Error creating database: OS error occurred - {err}")

    except Exception as e:
        err = e
        print(f"An unexpected error occurred while creating database - {err}")

    return err


@asynccontextmanager
async def get_session() -> AsyncGenerator[dict, None]:
    session = None
    try:
        session_data = json_parsef(db_file_name)
    except FileNotFoundError:
        # session_data = {}
        pass
    
    yield session_data
    
    
    with db_file_name.open("w") as file:
        file.write(json_stringify(session_data))