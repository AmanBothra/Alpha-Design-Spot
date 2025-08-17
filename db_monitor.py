#!/usr/bin/env python3
"""
Database Performance Monitor
Monitors PostgreSQL performance during load testing
"""

import psycopg2
import time
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any
import os
from threading import Thread
import signal
import sys


@dataclass
class DBMetrics:
    timestamp: str
    active_connections: int
    idle_connections: int
    total_connections: int
    max_connections: int
    connection_utilization: float
    queries_per_second: float
    avg_query_time_ms: float
    cache_hit_ratio: float
    deadlocks: int
    lock_waits: int
    temp_files: int
    temp_bytes: int


class DatabaseMonitor:
    def __init__(self):
        # Database connection parameters from .env
        self.db_params = {
            "host": os.getenv("DB_HOST", "localhost"),
            "database": "ads",
            "user": os.getenv("POSTGRES_USER", "postgres"),
            "password": os.getenv("POSTGRES_PASSWORD", "postgres"),
            "port": 5432,
        }
        self.monitoring = False
        self.metrics: List[DBMetrics] = []

    def get_db_connection(self):
        """Create database connection"""
        try:
            return psycopg2.connect(**self.db_params)
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return None

    def collect_metrics(self) -> DBMetrics:
        """Collect comprehensive database performance metrics"""
        conn = self.get_db_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cursor:
                # Get connection statistics
                cursor.execute(
                    """
                    SELECT 
                        COUNT(*) FILTER (WHERE state = 'active') as active_connections,
                        COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
                        COUNT(*) as total_connections,
                        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections
                    FROM pg_stat_activity 
                    WHERE datname = %s
                """,
                    (self.db_params["database"],),
                )

                conn_stats = cursor.fetchone()
                active_conn, idle_conn, total_conn, max_conn = conn_stats

                # Get query performance statistics
                cursor.execute(
                    """
                    SELECT 
                        COALESCE(SUM(calls), 0) as total_queries,
                        COALESCE(AVG(mean_exec_time), 0) as avg_query_time,
                        COALESCE(SUM(temp_blks_read + temp_blks_written), 0) as temp_blocks
                    FROM pg_stat_statements
                    WHERE dbid = (SELECT oid FROM pg_database WHERE datname = %s)
                """,
                    (self.db_params["database"],),
                )

                query_stats = cursor.fetchone()
                if query_stats and query_stats[0]:
                    total_queries, avg_query_time, temp_blocks = query_stats
                else:
                    total_queries, avg_query_time, temp_blocks = 0, 0, 0

                # Get cache hit ratio
                cursor.execute(
                    """
                    SELECT 
                        CASE 
                            WHEN (blks_hit + blks_read) = 0 THEN 100.0
                            ELSE (blks_hit::float / (blks_hit + blks_read)) * 100
                        END as cache_hit_ratio
                    FROM pg_stat_database 
                    WHERE datname = %s
                """,
                    (self.db_params["database"],),
                )

                cache_ratio = cursor.fetchone()[0] or 0

                # Get lock and deadlock statistics
                cursor.execute(
                    """
                    SELECT 
                        COALESCE(deadlocks, 0) as deadlocks,
                        COALESCE(conflicts, 0) as conflicts
                    FROM pg_stat_database 
                    WHERE datname = %s
                """,
                    (self.db_params["database"],),
                )

                lock_stats = cursor.fetchone()
                deadlocks, conflicts = lock_stats or (0, 0)

                # Get temp file usage
                cursor.execute(
                    """
                    SELECT 
                        COALESCE(temp_files, 0) as temp_files,
                        COALESCE(temp_bytes, 0) as temp_bytes
                    FROM pg_stat_database 
                    WHERE datname = %s
                """,
                    (self.db_params["database"],),
                )

                temp_stats = cursor.fetchone()
                temp_files, temp_bytes = temp_stats or (0, 0)

                connection_utilization = (
                    (total_conn / max_conn) * 100 if max_conn > 0 else 0
                )

                return DBMetrics(
                    timestamp=datetime.now().isoformat(),
                    active_connections=active_conn or 0,
                    idle_connections=idle_conn or 0,
                    total_connections=total_conn or 0,
                    max_connections=max_conn or 0,
                    connection_utilization=round(connection_utilization, 2),
                    queries_per_second=0,  # Will be calculated between samples
                    avg_query_time_ms=round(avg_query_time or 0, 2),
                    cache_hit_ratio=round(cache_ratio, 2),
                    deadlocks=deadlocks or 0,
                    lock_waits=conflicts or 0,
                    temp_files=temp_files or 0,
                    temp_bytes=temp_bytes or 0,
                )

        except Exception as e:
            print(f"❌ Error collecting metrics: {e}")
            return None
        finally:
            conn.close()

    def start_monitoring(self, interval: float = 1.0):
        """Start continuous monitoring"""
        self.monitoring = True
        print(f"🔍 Starting database monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop monitoring")

        last_queries = 0
        last_time = time.time()

        try:
            while self.monitoring:
                metrics = self.collect_metrics()
                if metrics:
                    # Calculate queries per second
                    current_time = time.time()
                    time_diff = current_time - last_time

                    if len(self.metrics) > 0 and time_diff > 0:
                        # This is approximate since pg_stat_statements is cumulative
                        metrics.queries_per_second = (
                            0  # Would need more complex calculation
                        )

                    self.metrics.append(metrics)

                    # Print current status
                    print(
                        f"🕒 {metrics.timestamp[:19]} | "
                        f"Connections: {metrics.active_connections}A/{metrics.idle_connections}I/{metrics.total_connections}T "
                        f"({metrics.connection_utilization}%) | "
                        f"Cache: {metrics.cache_hit_ratio}% | "
                        f"Avg Query: {metrics.avg_query_time_ms}ms"
                    )

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")

        self.monitoring = False

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False

    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze collected performance data"""
        if not self.metrics:
            return {"error": "No metrics collected"}

        # Connection analysis
        max_active = max(m.active_connections for m in self.metrics)
        avg_active = sum(m.active_connections for m in self.metrics) / len(self.metrics)
        max_utilization = max(m.connection_utilization for m in self.metrics)

        # Query performance analysis
        avg_query_times = [
            m.avg_query_time_ms for m in self.metrics if m.avg_query_time_ms > 0
        ]
        avg_query_time = (
            sum(avg_query_times) / len(avg_query_times) if avg_query_times else 0
        )

        # Cache performance
        cache_hit_ratios = [
            m.cache_hit_ratio for m in self.metrics if m.cache_hit_ratio > 0
        ]
        avg_cache_hit = (
            sum(cache_hit_ratios) / len(cache_hit_ratios) if cache_hit_ratios else 0
        )

        # Resource usage
        temp_file_usage = any(m.temp_files > 0 for m in self.metrics)
        deadlock_count = sum(m.deadlocks for m in self.metrics)

        analysis = {
            "monitoring_duration_minutes": len(self.metrics) / 60,
            "total_samples": len(self.metrics),
            "connection_analysis": {
                "max_active_connections": max_active,
                "avg_active_connections": round(avg_active, 1),
                "max_connection_utilization_percent": max_utilization,
                "connection_pool_size": 20,  # From settings
                "connection_pool_overflow": 10,  # From settings
            },
            "query_performance": {
                "avg_query_time_ms": round(avg_query_time, 2),
                "slow_queries_detected": avg_query_time > 100,
            },
            "cache_performance": {
                "avg_cache_hit_ratio_percent": round(avg_cache_hit, 2),
                "cache_performance_good": avg_cache_hit > 95,
            },
            "resource_issues": {
                "temp_files_used": temp_file_usage,
                "deadlocks_detected": deadlock_count > 0,
                "total_deadlocks": deadlock_count,
            },
            "recommendations": self.get_performance_recommendations(
                max_active,
                max_utilization,
                avg_query_time,
                avg_cache_hit,
                deadlock_count,
            ),
        }

        return analysis

    def get_performance_recommendations(
        self,
        max_active: int,
        max_util: float,
        avg_query_time: float,
        cache_hit: float,
        deadlocks: int,
    ) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        # Connection pool recommendations
        if max_util > 80:
            recommendations.append(
                "🔥 High connection utilization - consider increasing pool size"
            )
        elif max_util > 60:
            recommendations.append(
                "⚠️ Moderate connection utilization - monitor closely"
            )

        if max_active > 15:  # 75% of pool size
            recommendations.append(
                "📊 High active connections - optimize query efficiency"
            )

        # Query performance recommendations
        if avg_query_time > 500:
            recommendations.append(
                "🐌 Slow queries detected - review and optimize database queries"
            )
        elif avg_query_time > 100:
            recommendations.append(
                "⏱️ Moderate query times - consider query optimization"
            )

        # Cache recommendations
        if cache_hit < 90:
            recommendations.append(
                "💾 Low cache hit ratio - consider increasing shared_buffers"
            )
        elif cache_hit < 95:
            recommendations.append("📈 Cache hit ratio could be improved")

        # Resource issue recommendations
        if deadlocks > 0:
            recommendations.append(
                "🔒 Deadlocks detected - review transaction handling and query order"
            )

        if not recommendations:
            recommendations.append("✅ Database performance looks healthy!")

        return recommendations

    def save_report(self, filename: str = None):
        """Save monitoring report to file"""
        if not filename:
            timestamp = int(time.time())
            filename = f"db_monitor_report_{timestamp}.json"

        analysis = self.analyze_performance()

        report = {
            "monitoring_session": {
                "start_time": self.metrics[0].timestamp if self.metrics else None,
                "end_time": self.metrics[-1].timestamp if self.metrics else None,
                "sample_count": len(self.metrics),
            },
            "performance_analysis": analysis,
            "raw_metrics": [
                {
                    "timestamp": m.timestamp,
                    "active_connections": m.active_connections,
                    "total_connections": m.total_connections,
                    "connection_utilization": m.connection_utilization,
                    "avg_query_time_ms": m.avg_query_time_ms,
                    "cache_hit_ratio": m.cache_hit_ratio,
                }
                for m in self.metrics
            ],
        }

        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Database monitoring report saved to: {filename}")
        return filename


def main():
    """Main monitoring function"""
    monitor = DatabaseMonitor()

    # Test database connection
    conn = monitor.get_db_connection()
    if not conn:
        print(
            "❌ Cannot connect to database. Please check your database configuration."
        )
        return
    conn.close()

    print("✅ Database connection successful")

    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Stopping database monitor...")
        monitor.stop_monitoring()

        # Generate and save report
        if monitor.metrics:
            report_file = monitor.save_report()
            analysis = monitor.analyze_performance()

            print("\n" + "=" * 60)
            print("📊 DATABASE PERFORMANCE SUMMARY")
            print("=" * 60)

            conn_analysis = analysis.get("connection_analysis", {})
            print(
                f"Max Active Connections: {conn_analysis.get('max_active_connections', 0)}"
            )
            print(
                f"Max Utilization: {conn_analysis.get('max_connection_utilization_percent', 0)}%"
            )

            query_perf = analysis.get("query_performance", {})
            print(f"Avg Query Time: {query_perf.get('avg_query_time_ms', 0)}ms")

            cache_perf = analysis.get("cache_performance", {})
            print(
                f"Cache Hit Ratio: {cache_perf.get('avg_cache_hit_ratio_percent', 0)}%"
            )

            print("\n📋 Recommendations:")
            for rec in analysis.get("recommendations", []):
                print(f"  {rec}")

        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Start monitoring
    monitor.start_monitoring(interval=1.0)


if __name__ == "__main__":
    main()
