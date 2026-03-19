#!/usr/bin/env python3
"""
Celery Worker CLI
启动和管理 Celery Worker
"""

import click
import sys
import os

# 确保能找到项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from skyone_shuge.core.celery_app import celery_app

@click.group()
def worker():
    """Celery Worker 管理命令"""
    pass

@worker.command()
@click.option("--name", default="worker1", help="Worker 名称")
@click.option("--log-level", default="info", help="日志级别 (debug/info/warning/error)")
@click.option("--concurrency", default=4, help="并发数")
@click.option("--queues", default="documents,embeddings,index,notifications", help="监听的队列，逗号分隔")
def start(name: str, log_level: str, concurrency: int, queues: str):
    """启动 Celery Worker"""
    click.echo(f"🚀 Starting Celery Worker: {name}")
    click.echo(f"   Log Level: {log_level}")
    click.echo(f"   Concurrency: {concurrency}")
    click.echo(f"   Queues: {queues}")
    
    celery_app.worker_main([
        "worker",
        f"--hostname={name}@%h",
        f"--loglevel={log_level}",
        f"--concurrency={concurrency}",
        f"--queues={queues}",
        "-E"  # 启用事件以便监控
    ])

@worker.command()
def status():
    """查看 Worker 状态"""
    inspect = celery_app.control.inspect()
    
    click.echo("正在查询 Worker 状态...")
    active = inspect.active()
    stats = inspect.stats()
    
    click.echo("\n📊 Celery Worker 状态")
    click.echo("=" * 40)
    
    if stats:
        for worker_name, info in stats.items():
            click.echo(f"Worker: {worker_name}")
            
            # 活动任务
            worker_active = active.get(worker_name, [])
            click.echo(f"  - 正在处理: {len(worker_active)} 个任务")
            for task in worker_active:
                click.echo(f"    * [{task['id']}] {task['name']}")
                
            # 统计信息
            total_tasks = info.get('total', {})
            click.echo(f"  - 历史总计: {sum(total_tasks.values())} 个任务")
            
            click.echo("-" * 40)
    else:
        click.echo("❌ 未发现活跃的 Worker。请确保 Worker 已启动并且 Redis 连接正常。")

if __name__ == "__main__":
    worker()
