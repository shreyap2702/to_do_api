from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, SQLModel, Session, create_engine, select

class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task: str = Field(index = True)
    description: str
    time: int | None = Field(default=None, index=True)
    
    
#create an engine

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/tasks/")
def create_task(task : Task, session : SessionDep):
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@app.get("/tasks/")
def read_tasks(session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le = 100)] = 10,)->list[Task]:
    tasks = session.exec(select(Task).offset(offset).limit(limit)).all()
    return tasks

@app.get("/tasks/{task_id}")
def read_task(task_id : int, session : SessionDep) -> Task:
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int,session : SessionDep):
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)
    session.commit()
    return {"ok": True}

