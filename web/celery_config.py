broker_url = "redis://localhost:6379/10"
redbeat_redis_url = "redis://localhost:6379/11"

# result_backend = 'mongodb://localhost:27017/webSpeed'
beat_scheduler = "redbeat.RedBeatScheduler"

beat_max_loop_interval = (
    5  # The maximum number of seconds beat can sleep between checking the schedule
)
redbeat_key_prefix = "redbeat"

# beat_schedule = {
#     "daily_summary": {
#         "task": "worker.daily_summary",
#         "schedule": 120.0,
#         "name": "daily-summary",
#     }
# }
