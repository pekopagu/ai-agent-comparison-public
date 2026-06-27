import datetime
import random
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend import models, schemas

# List of pleasant colors for tags
TAG_COLORS = [
    "#6366f1",  # indigo
    "#10b981",  # emerald
    "#f59e0b",  # amber
    "#3b82f6",  # blue
    "#8b5cf6",  # purple
    "#ec4899",  # pink
    "#14b8a6",  # teal
    "#06b6d4",  # cyan
    "#f97316",  # orange
    "#a855f7"   # violet
]

def get_or_create_tags_by_name(db: Session, tag_names: list[str]) -> list[models.Tag]:
    tags = []
    for name in tag_names:
        name_stripped = name.strip()
        if not name_stripped:
            continue
        # Case-insensitive check or direct unique match
        tag = db.query(models.Tag).filter(func.lower(models.Tag.name) == func.lower(name_stripped)).first()
        if not tag:
            # Generate a random color or pick one from the pool
            color = random.choice(TAG_COLORS)
            tag = models.Tag(name=name_stripped, color=color)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        tags.append(tag)
    return tags

# --- Tag CRUD ---
def get_tags(db: Session) -> list[models.Tag]:
    return db.query(models.Tag).all()

def create_tag(db: Session, tag_in: schemas.TagCreate) -> models.Tag:
    tag = models.Tag(name=tag_in.name.strip(), color=tag_in.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

def delete_tag(db: Session, tag_id: int) -> bool:
    tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if tag:
        db.delete(tag)
        db.commit()
        return True
    return False

# --- Task CRUD ---
def get_tasks(
    db: Session,
    status: str = None,
    priority: str = None,
    tag: str = None,
    search: str = None
) -> list[models.Task]:
    query = db.query(models.Task)

    if status:
        query = query.filter(models.Task.status == status)
    
    if priority:
        query = query.filter(models.Task.priority == priority)
        
    if tag:
        query = query.join(models.Task.tags).filter(func.lower(models.Tag.name) == func.lower(tag))
        
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            models.Task.title.ilike(search_term) | 
            models.Task.description.ilike(search_term)
        )
        
    # Order by due_date nulls last, then created_at desc
    # In SQLite, we can order by: case when due_date is null then 1 else 0 end, due_date asc
    # Let's keep it simple: order by created_at desc
    return query.order_by(models.Task.created_at.desc()).all()

def get_task_by_id(db: Session, task_id: int) -> models.Task:
    return db.query(models.Task).filter(models.Task.id == task_id).first()

def create_task(db: Session, task_in: schemas.TaskCreate) -> models.Task:
    now_str = datetime.datetime.now().isoformat()
    db_tags = get_or_create_tags_by_name(db, task_in.tags) if task_in.tags else []

    task = models.Task(
        title=task_in.title,
        description=task_in.description,
        status=task_in.status,
        priority=task_in.priority,
        due_date=task_in.due_date,
        created_at=now_str,
        updated_at=now_str,
        tags=db_tags
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def update_task(db: Session, task_id: int, task_in: schemas.TaskUpdate) -> models.Task:
    task = get_task_by_id(db, task_id)
    if not task:
        return None
    
    # Update fields if provided
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "tags":
            continue # Handle separately
        setattr(task, field, value)
        
    # Handle tag updates if provided
    if task_in.tags is not None:
        db_tags = get_or_create_tags_by_name(db, task_in.tags)
        task.tags = db_tags

    task.updated_at = datetime.datetime.now().isoformat()
    db.commit()
    db.refresh(task)
    return task

def delete_task(db: Session, task_id: int) -> bool:
    task = get_task_by_id(db, task_id)
    if task:
        db.delete(task)
        db.commit()
        return True
    return False

# --- Analytics CRUD ---
def get_analytics(db: Session) -> schemas.AnalyticsSummary:
    total = db.query(models.Task).count()
    todo = db.query(models.Task).filter(models.Task.status == "todo").count()
    in_progress = db.query(models.Task).filter(models.Task.status == "in_progress").count()
    done = db.query(models.Task).filter(models.Task.status == "done").count()
    high = db.query(models.Task).filter(models.Task.priority == "high").count()
    
    today_str = datetime.date.today().isoformat()
    # Overdue tasks are not done and have a due_date earlier than today
    overdue = db.query(models.Task).filter(
        models.Task.status != "done",
        models.Task.due_date.isnot(None),
        models.Task.due_date != "",
        models.Task.due_date < today_str
    ).count()
    
    completion_rate = round((done / total * 100), 1) if total > 0 else 0.0
    
    return schemas.AnalyticsSummary(
        total_tasks=total,
        todo_tasks=todo,
        in_progress_tasks=in_progress,
        done_tasks=done,
        completion_rate=completion_rate,
        high_priority_tasks=high,
        overdue_tasks=overdue
    )
