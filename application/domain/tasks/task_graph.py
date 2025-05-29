from application.domain.tasks.task import TaskState

class TaskGraph:
    def __init__(self, tasks):
        self.tasks = {t.id: t for t in tasks}
        self.completed = set()
        self._check_for_cycles()  # 👈 初始化时检测

    def _check_for_cycles(self):
        visited = set()
        stack = set()

        def visit(task_id):
            if task_id in stack:
                raise ValueError(f"任务依赖图存在循环：{task_id} 形成了回环")
            if task_id not in visited:
                stack.add(task_id)
                for dep in self.tasks[task_id].depends_on:
                    if dep not in self.tasks:
                        raise ValueError(f"依赖任务不存在：{task_id} → {dep}")
                    visit(dep)
                stack.remove(task_id)
                visited.add(task_id)

        for task_id in self.tasks:
            visit(task_id)

    def get_runnable_tasks(self):
        return [t for t in self.tasks.values()
                if t.state == TaskState.PENDING and t.is_ready(self.completed)]

    def mark_done(self, task_id):
        self.completed.add(task_id)
