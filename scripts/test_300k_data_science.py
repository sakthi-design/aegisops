import time
import random
from backend.temporal.profiler import DatasetStatisticalProfiler

print("Generating 300,000 synthetic records...")
t0 = time.time()
rows = ["number,incident_state,active,reassignment_count,reopen_count,sys_created_at,sys_updated_at,opened_at,resolved_at,closed_at,priority,urgency,severity,category,made_sla"]
priorities = ["1 - Critical", "2 - High", "3 - Moderate", "4 - Low"]
slas = ["true", "true", "true", "false"]

for i in range(300000):
    p = random.choice(priorities)
    sla = random.choice(slas)
    cat = f"Category {random.randint(1, 10)}"
    rows.append(f"INC{i:06d},closed,false,0,0,2026-01-01 10:00,2026-01-02 12:00,2026-01-01 10:00,2026-01-02 12:00,2026-01-02 12:00,{p},2,2,{cat},{sla}")

content = "\n".join(rows)
t1 = time.time()
print(f"Generated 300k rows in {t1 - t0:.2f}s.")

print("Profiling 300k rows with DatasetStatisticalProfiler...")
t2 = time.time()
stats = DatasetStatisticalProfiler.profile_content(content, filename="300k_incidents.csv")
t3 = time.time()

print(f"DONE in {t3 - t2:.2f} seconds!")
print(f"Total Records Profiled: {stats['total_records']:,}")
print(f"Critical Alerts: {stats['critical_count']:,}")
print(f"High Alerts: {stats['high_count']:,}")
print(f"SLA Breached: {stats['sla_breached_count']:,} ({stats['sla_breach_rate_pct']}%)")
print(f"Mean MTTR: {stats['mean_mttr_sec']/3600.0:.2f} hours")
print(f"P50 MTTR: {stats['p50_mttr_sec']/3600.0:.2f} hours")
print(f"Top 3 Categories: {stats['top_categories'][:3]}")
