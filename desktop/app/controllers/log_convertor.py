import json
from app import schemas as s

from app.consts import OUTPUT_LOG_FILE_PATH, INPUT_LOG_FILE_PATH


def log_convertor():
    with open(INPUT_LOG_FILE_PATH, "r", encoding="utf-8") as i_f:
        with open(OUTPUT_LOG_FILE_PATH, "w", encoding="utf-8") as o_f:
            line_no = 1
            try:
                for line in i_f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    log_line = s.LogLine.model_validate_json(line)
                    o_f.writelines(
                        [
                            f"{log_line.record.time.repr}:{log_line.record.module}:{log_line.record.level.name}:{log_line.record.message}",
                            "\n",
                        ]
                    )
                    if log_line.record.exception and log_line.record.exception.traceback:
                        o_f.write(log_line.text)
                    line_no += 1
            except UnicodeDecodeError as e:
                print(f"Line {line_no} is not valid json. Error: {e}")
