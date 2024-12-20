# src/utils/scheduler.py

from typing import Dict, Callable, Optional, Any
import asyncio
import logging
from datetime import datetime, timedelta
import json
from dataclasses import dataclass
import traceback

logger = logging.getLogger(__name__)

@dataclass
class ScheduledTask:
    """מידע על משימה מתוזמנת"""
    name: str
    func: Callable
    interval: int  # seconds
    last_run: Optional[datetime] = None
    is_running: bool = False
    error_count: int = 0
    max_errors: int = 3
    args: tuple = ()
    kwargs: Dict[str, Any] = None
    
    def __post_init__(self):
        self.kwargs = self.kwargs or {}

class TaskScheduler:
    """מנהל משימות מתוזמנות"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running = False
        self._lock = asyncio.Lock()
        
        # זמני ברירת מחדל למשימות (בשניות)
        self.default_intervals = {
            "knowledge_update": 3600,      # עדכון ידע כל שעה
            "metrics_cleanup": 86400,      # ניקוי מטריקות כל יום
            "system_backup": 43200,        # גיבוי כל 12 שעות
            "health_check": 300,           # בדיקת בריאות כל 5 דקות
            "error_notification": 1800     # בדיקת שגיאות כל 30 דקות
        }

    async def start(self):
        """התחלת מנהל המשימות"""
        if self.running:
            return
            
        self.running = True
        asyncio.create_task(self._run_scheduler())
        logger.info("Task scheduler started")

    async def stop(self):
        """עצירת מנהל המשימות"""
        self.running = False
        # חכה שכל המשימות הפעילות יסתיימו
        await asyncio.gather(
            *(self._wait_for_task(task) for task in self.tasks.values() if task.is_running)
        )
        logger.info("Task scheduler stopped")

    async def add_task(
        self,
        name: str,
        func: Callable,
        interval: Optional[int] = None,
        **kwargs
    ):
        """הוספת משימה חדשה"""
        async with self._lock:
            if name in self.tasks:
                raise ValueError(f"Task {name} already exists")
                
            # אם לא צוין מרווח זמן, השתמש בברירת המחדל
            if interval is None:
                interval = self.default_intervals.get(name, 3600)
            
            task = ScheduledTask(
                name=name,
                func=func,
                interval=interval,
                kwargs=kwargs
            )
            
            self.tasks[name] = task
            logger.info(f"Added task: {name} with interval {interval}s")

    async def remove_task(self, name: str):
        """הסרת משימה"""
        async with self._lock:
            if name not in self.tasks:
                raise ValueError(f"Task {name} not found")
                
            task = self.tasks[name]
            if task.is_running:
                await self._wait_for_task(task)
                
            del self.tasks[name]
            logger.info(f"Removed task: {name}")

    async def _run_scheduler(self):
        """הרצת לולאת המשימות המתוזמנות"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                for task in self.tasks.values():
                    # בדוק אם צריך להריץ את המשימה
                    if (not task.is_running and 
                        (task.last_run is None or 
                         (current_time - task.last_run).total_seconds() >= task.interval)):
                        asyncio.create_task(self._execute_task(task))
                
                await asyncio.sleep(1)  # בדיקה כל שנייה
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                await asyncio.sleep(5)  # המתן לפני ניסיון נוסף

    async def _execute_task(self, task: ScheduledTask):
        """הרצת משימה בודדת"""
        try:
            task.is_running = True
            task.last_run = datetime.utcnow()
            
            logger.debug(f"Executing task: {task.name}")
            
            # הרץ את המשימה
            if asyncio.iscoroutinefunction(task.func):
                await task.func(*task.args, **task.kwargs)
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, task.func, *task.args, **task.kwargs
                )
            
            # אפס את מונה השגיאות אחרי הרצה מוצלחת
            task.error_count = 0
            
        except Exception as e:
            task.error_count += 1
            logger.error(
                f"Error executing task {task.name} "
                f"(error {task.error_count}/{task.max_errors}): {str(e)}\n"
                f"{traceback.format_exc()}"
            )
            
            if task.error_count >= task.max_errors:
                logger.critical(
                    f"Task {task.name} exceeded maximum error count. Disabling task."
                )
                await self.remove_task(task.name)
                
        finally:
            task.is_running = False

    async def _wait_for_task(self, task: ScheduledTask, timeout: int = 30):
        """המתנה לסיום משימה"""
        start_time = datetime.utcnow()
        while task.is_running:
            if (datetime.utcnow() - start_time).total_seconds() > timeout:
                logger.warning(f"Timeout waiting for task {task.name} to complete")
                break
            await asyncio.sleep(0.1)

    async def get_status(self) -> Dict:
        """קבלת סטטוס כל המשימות"""
        return {
            name: {
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "is_running": task.is_running,
                "error_count": task.error_count,
                "interval": task.interval,
                "next_run": (
                    (task.last_run + timedelta(seconds=task.interval)).isoformat()
                    if task.last_run else datetime.utcnow().isoformat()
                )
            }
            for name, task in self.tasks.items()
        }

    async def update_interval(self, name: str, interval: int):
        """עדכון מרווח הזמן של משימה"""
        async with self._lock:
            if name not in self.tasks:
                raise ValueError(f"Task {name} not found")
                
            self.tasks[name].interval = interval
            logger.info(f"Updated interval for task {name} to {interval}s")

    async def run_task_now(self, name: str):
        """הרצה מיידית של משימה"""
        if name not in self.tasks:
            raise ValueError(f"Task {name} not found")
            
        task = self.tasks[name]
        if task.is_running:
            raise RuntimeError(f"Task {name} is already running")
            
        # אפס את זמן ההרצה האחרון כדי שהמשימה תרוץ מיד
        task.last_run = None
        logger.info(f"Triggered immediate execution of task {name}")